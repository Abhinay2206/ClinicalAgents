"""
Async MongoDB storage layer for chat memory, audit logs, and backups.

Environment variables:
- MONGODB_URI: MongoDB connection string
- MONGODB_DB: Database name (default: ClinicalAgents)

Collections:
- chat_memory: per-turn chat messages and agent outputs
- audit_logs: detailed event logs across the pipeline
- backups: periodic session snapshots for rollback
"""
from __future__ import annotations

import os
import asyncio
import datetime as dt
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Only for type checkers
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore
else:
    AsyncIOMotorClient = Any  # type: ignore
    AsyncIOMotorDatabase = Any  # type: ignore


class AsyncMongoStore:
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self._uri = uri or os.getenv("MONGODB_URI") or "mongodb://localhost:27017"
        self._db_name = db_name or os.getenv("MONGODB_DB") or "ClinicalAgents"
        self._client: Optional[Any] = None
        self._db: Optional[Any] = None
        self._lock = asyncio.Lock()

    async def _ensure_connected(self):
        if (self._client is not None) and (self._db is not None):
            return
        async with self._lock:
            if (self._client is not None) and (self._db is not None):
                return
            try:
                from motor.motor_asyncio import AsyncIOMotorClient as _Client  # type: ignore
            except Exception as _e:  # pragma: no cover
                raise RuntimeError("motor is not installed. Add 'motor' to requirements.txt and install it.")
            self._client = _Client(self._uri, serverSelectionTimeoutMS=5000)
            # Trigger a ping to verify connection
            await self._client.admin.command("ping")
            self._db = self._client[self._db_name]
            await self._ensure_indexes()

    async def _ensure_indexes(self):
        assert self._db is not None
        await self._db["chat_memory"].create_index([("session_id", 1), ("timestamp", 1)])
        await self._db["audit_logs"].create_index([("session_id", 1), ("timestamp", 1)])
        await self._db["backups"].create_index([("session_id", 1), ("created_at", 1)])

    @property
    def db_name(self) -> str:
        return self._db_name

    # ---------- Chat Memory ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def save_chat_message(self, session_id: str, role: str, content: str, agent_outputs: Optional[Dict[str, Any]] = None) -> str:
        await self._ensure_connected()
        assert self._db is not None
        doc = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "agent_outputs": agent_outputs or {},
            "timestamp": dt.datetime.utcnow(),
        }
        res = await self._db["chat_memory"].insert_one(doc)
        return str(res.inserted_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        await self._ensure_connected()
        assert self._db is not None
        cursor = self._db["chat_memory"].find({"session_id": session_id}).sort("timestamp", 1)
        return [doc async for doc in cursor]

    # ---------- Audit Logs ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def log_event(self, session_id: str, event: str, agent_name: str, content: Dict[str, Any], status: str = "info") -> str:
        await self._ensure_connected()
        assert self._db is not None
        doc = {
            "session_id": session_id,
            "event": event,
            "agent_name": agent_name,
            "content": content,
            "status": status,
            "timestamp": dt.datetime.utcnow(),
        }
        res = await self._db["audit_logs"].insert_one(doc)
        return str(res.inserted_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def get_audit_logs(self, session_id: str) -> List[Dict[str, Any]]:
        await self._ensure_connected()
        assert self._db is not None
        cursor = self._db["audit_logs"].find({"session_id": session_id}).sort("timestamp", 1)
        return [doc async for doc in cursor]

    # ---------- Backups ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def snapshot_session(self, session_id: str) -> str:
        await self._ensure_connected()
        assert self._db is not None
        history = await self.get_session_history(session_id)
        audits = await self.get_audit_logs(session_id)
        snapshot = {
            "session_id": session_id,
            "created_at": dt.datetime.utcnow(),
            "chat_memory": history,
            "audit_logs": audits,
        }
        res = await self._db["backups"].insert_one(snapshot)
        return str(res.inserted_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def list_sessions(self, limit: int = 50) -> List[str]:
        await self._ensure_connected()
        assert self._db is not None
        # Distinct can be expensive; for small scale it's acceptable
        sessions = await self._db["chat_memory"].distinct("session_id")
        return sessions[:limit]
