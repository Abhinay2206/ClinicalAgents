from __future__ import annotations

import os
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from gemini_client import GeminiClient
from agents.human_proxy_agent import HumanProxyAgent
from storage.mongo_async import AsyncMongoStore
from simple_dynamic_orchestrator import SimpleDynamicOrchestrator


class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None


load_dotenv()
app = FastAPI(title="ClinicalAgents API", version="0.1.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _new_proxy(session_id: Optional[str] = None) -> HumanProxyAgent:
    llm = GeminiClient(model_name="gemini-2.5-flash")
    store = AsyncMongoStore()
    orchestrator = SimpleDynamicOrchestrator(llm)
    return HumanProxyAgent(llm, store=store, orchestrator=orchestrator, session_id=session_id)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "use_proxy": os.getenv("USE_PROXY", "1") != "0"}


@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")
    proxy = _new_proxy(session_id=req.session_id)
    result = await proxy.handle_user_prompt_async(req.prompt)
    return result


@app.get("/history/{session_id}")
async def history(session_id: str):
    proxy = _new_proxy(session_id=session_id)
    data = await proxy.fetch_session_history(session_id)
    return data


@app.get("/replay/{session_id}")
async def replay(session_id: str):
    proxy = _new_proxy(session_id=session_id)
    data = await proxy.replay_session(session_id)
    return data


if __name__ == "__main__":
    # Allow running with: python api.py
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8000"))
    except Exception:
        port = 8000
    reload = os.getenv("RELOAD", "1") != "0"

    print(f"Starting ClinicalAgents API on http://{host}:{port} (reload={reload})")
    print("Docs: http://127.0.0.1:8000/docs")
    # When reload is enabled, uvicorn requires an import string
    if reload:
        # Running from agents_server directory; module is 'app'
        uvicorn.run("app:app", host=host, port=port, reload=True)
    else:
        uvicorn.run(app, host=host, port=port, reload=False)
