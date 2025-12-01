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
        self._uri = uri or os.getenv("MONGODB_URI")
        self._db_name = db_name or os.getenv("MONGODB_DB") or "ClinicalAgents"
        self._client: Optional[Any] = None
        self._db: Optional[Any] = None
        self._lock = asyncio.Lock()
        self._indexes_created = False
        self._mongo_available = self._uri is not None
        self._connection_failed = False

    async def _ensure_connected(self):
        # If MongoDB is not configured or connection previously failed, skip
        if not self._mongo_available:
            return False
        if self._connection_failed:
            return False
            
        if (self._client is not None) and (self._db is not None):
            return True
            
        async with self._lock:
            if (self._client is not None) and (self._db is not None):
                return True
                
            try:
                from motor.motor_asyncio import AsyncIOMotorClient as _Client  # type: ignore
            except Exception as _e:  # pragma: no cover
                print("⚠️  Warning: motor is not installed. MongoDB features disabled.")
                self._connection_failed = True
                return False
                
            try:
                # Reduced timeout and connection pooling
                self._client = _Client(
                    self._uri,
                    serverSelectionTimeoutMS=2000,  # Reduced from 5s to 2s
                    connectTimeoutMS=2000,
                    socketTimeoutMS=5000,
                    maxPoolSize=10,
                    minPoolSize=1
                )
                # Trigger a ping to verify connection with timeout
                await asyncio.wait_for(self._client.admin.command("ping"), timeout=2.0)
                self._db = self._client[self._db_name]
                # Only create indexes once
                if not self._indexes_created:
                    await self._ensure_indexes()
                    self._indexes_created = True
                print(f"✓ MongoDB connected to {self._db_name}")
                return True
            except asyncio.TimeoutError:
                print("⚠️  Warning: MongoDB connection timeout - running without persistence")
                self._connection_failed = True
                return False
            except Exception as e:
                print(f"⚠️  Warning: MongoDB connection failed ({str(e)}) - running without persistence")
                self._connection_failed = True
                return False

    async def _ensure_indexes(self):
        assert self._db is not None
        # User indexes
        await self._db["users"].create_index([("email", 1)], unique=True)
        
        # Session indexes
        await self._db["sessions"].create_index([("user_id", 1), ("created_at", -1)])
        await self._db["sessions"].create_index([("id", 1)], unique=True)
        
        # Chat memory indexes - updated to support user_id
        await self._db["chat_memory"].create_index([("user_id", 1), ("session_id", 1), ("timestamp", 1)])
        await self._db["chat_memory"].create_index([("session_id", 1), ("timestamp", 1)])
        
        # Audit logs
        await self._db["audit_logs"].create_index([("session_id", 1), ("timestamp", 1)])
        await self._db["backups"].create_index([("session_id", 1), ("created_at", 1)])

    @property
    def db_name(self) -> str:
        return self._db_name

    # ---------- Chat Memory ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def save_chat_message(self, session_id: str, role: str, content: str, agent_outputs: Optional[Dict[str, Any]] = None) -> str:
        if not await self._ensure_connected():
            return ""  # MongoDB unavailable, skip persistence
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
        if not await self._ensure_connected():
            return []  # MongoDB unavailable, return empty history
        assert self._db is not None
        cursor = self._db["chat_memory"].find({"session_id": session_id}).sort("timestamp", 1)
        docs = [doc async for doc in cursor]
        # Convert ObjectId and datetime to string for JSON serialization
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            if "timestamp" in doc and hasattr(doc["timestamp"], "isoformat"):
                doc["timestamp"] = doc["timestamp"].isoformat()
        return docs

    # ---------- Audit Logs ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def log_event(self, session_id: str, event: str, agent_name: str, content: Dict[str, Any], status: str = "info") -> str:
        if not await self._ensure_connected():
            return ""  # MongoDB unavailable, skip logging
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
        if not await self._ensure_connected():
            return []  # MongoDB unavailable, return empty logs
        assert self._db is not None
        cursor = self._db["audit_logs"].find({"session_id": session_id}).sort("timestamp", 1)
        docs = [doc async for doc in cursor]
        # Convert ObjectId and datetime to string for JSON serialization
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            if "timestamp" in doc and hasattr(doc["timestamp"], "isoformat"):
                doc["timestamp"] = doc["timestamp"].isoformat()
        return docs

    # ---------- Backups ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def snapshot_session(self, session_id: str) -> str:
        if not await self._ensure_connected():
            return ""  # MongoDB unavailable, skip snapshot
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
        if not await self._ensure_connected():
            return []  # MongoDB unavailable, return empty list
        assert self._db is not None
        # Distinct can be expensive; for small scale it's acceptable
        sessions = await self._db["chat_memory"].distinct("session_id")
        return sessions[:limit]

    # ---------- User Management ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def create_user(self, email: str, hashed_password: str, name: str) -> Dict[str, Any]:
        """Create a new user"""
        if not await self._ensure_connected():
            raise Exception("MongoDB unavailable")
        assert self._db is not None
        
        from bson import ObjectId
        user_id = str(ObjectId())
        
        doc = {
            "id": user_id,
            "email": email,
            "hashed_password": hashed_password,
            "name": name,
            "created_at": dt.datetime.utcnow().isoformat(),
            "is_active": True,
        }
        await self._db["users"].insert_one(doc)
        return doc

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        if not await self._ensure_connected():
            return None
        assert self._db is not None
        
        user = await self._db["users"].find_one({"email": email})
        if user and "_id" in user:
            user["_id"] = str(user["_id"])
        return user

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if not await self._ensure_connected():
            return None
        assert self._db is not None
        
        user = await self._db["users"].find_one({"id": user_id})
        if user and "_id" in user:
            user["_id"] = str(user["_id"])
        return user

    # ---------- Session Management ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def create_session(self, user_id: str, title: str = "New Chat") -> Dict[str, Any]:
        """Create a new chat session for a user"""
        if not await self._ensure_connected():
            raise Exception("MongoDB unavailable")
        assert self._db is not None
        
        from bson import ObjectId
        session_id = str(ObjectId())
        
        doc = {
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": dt.datetime.utcnow().isoformat(),
            "updated_at": dt.datetime.utcnow().isoformat(),
        }
        await self._db["sessions"].insert_one(doc)
        return doc

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        if not await self._ensure_connected():
            return []
        assert self._db is not None
        
        cursor = self._db["sessions"].find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        sessions = [doc async for doc in cursor]
        
        # Convert ObjectId to string
        for session in sessions:
            if "_id" in session:
                session["_id"] = str(session["_id"])
        
        return sessions

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID"""
        if not await self._ensure_connected():
            return None
        assert self._db is not None
        
        session = await self._db["sessions"].find_one({"id": session_id})
        if session and "_id" in session:
            session["_id"] = str(session["_id"])
        return session

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        if not await self._ensure_connected():
            return False
        assert self._db is not None
        
        result = await self._db["sessions"].update_one(
            {"id": session_id},
            {"$set": {"title": title, "updated_at": dt.datetime.utcnow().isoformat()}}
        )
        return result.modified_count > 0

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        if not await self._ensure_connected():
            return False
        assert self._db is not None
        
        # Delete session document
        await self._db["sessions"].delete_one({"id": session_id})
        
        # Delete all messages in this session
        await self._db["chat_memory"].delete_many({"session_id": session_id})
        
        # Delete audit logs
        await self._db["audit_logs"].delete_many({"session_id": session_id})
        
        return True

    # ---------- Updated Chat Memory with User ID ----------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def save_chat_message_with_user(
        self, 
        user_id: str, 
        session_id: str, 
        role: str, 
        content: str, 
        agent_outputs: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save chat message with user_id"""
        if not await self._ensure_connected():
            return ""
        assert self._db is not None
        
        doc = {
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "agent_outputs": agent_outputs or {},
            "timestamp": dt.datetime.utcnow(),
        }
        res = await self._db["chat_memory"].insert_one(doc)
        return str(res.inserted_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def get_session_history_for_user(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Get session history, ensuring it belongs to the user"""
        if not await self._ensure_connected():
            return []
        assert self._db is not None
        
        cursor = self._db["chat_memory"].find({
            "user_id": user_id,
            "session_id": session_id
        }).sort("timestamp", 1)
        
        docs = [doc async for doc in cursor]
        
        # Convert ObjectId and datetime to string
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            if "timestamp" in doc and hasattr(doc["timestamp"], "isoformat"):
                doc["timestamp"] = doc["timestamp"].isoformat()
        
        return docs
