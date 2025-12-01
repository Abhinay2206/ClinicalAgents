from __future__ import annotations

import os
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from gemini_client import GeminiClient
from agents.human_proxy_agent import HumanProxyAgent
from storage.mongo_async import AsyncMongoStore
from simple_dynamic_orchestrator import SimpleDynamicOrchestrator
from models import UserRegister, UserLogin, TokenResponse, UserResponse, SessionCreate, SessionResponse
from auth import (
    get_password_hash, 
    verify_password, 
    create_user_token, 
    get_current_user,
    security
)
from fastapi.security import HTTPAuthorizationCredentials


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

# Global singletons for performance - initialized once at startup
_llm_client: Optional[GeminiClient] = None
_mongo_store: Optional[AsyncMongoStore] = None
_orchestrator: Optional[SimpleDynamicOrchestrator] = None


@app.on_event("startup")
async def startup_event():
    """Initialize expensive resources once at startup"""
    global _llm_client, _mongo_store, _orchestrator
    print("🚀 Initializing application resources...")
    
    # Initialize LLM client (lightweight)
    _llm_client = GeminiClient(model_name="gemini-2.5-flash")
    print("✓ LLM client initialized")
    
    # Initialize MongoDB store (connection pool)
    _mongo_store = AsyncMongoStore()
    print("✓ MongoDB store initialized")
    
    # Initialize orchestrator with all agents (heavy - do once)
    _orchestrator = SimpleDynamicOrchestrator(_llm_client)
    print("✓ Orchestrator and agents initialized")
    print("🎉 Application ready!")


def _new_proxy(session_id: Optional[str] = None) -> HumanProxyAgent:
    """Create a lightweight proxy using shared resources"""
    return HumanProxyAgent(
        llm=_llm_client,
        store=_mongo_store,
        orchestrator=_orchestrator,
        session_id=session_id
    )


# Dependency to inject store into get_current_user
async def get_current_user_with_store(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """Get current user with store injected"""
    return await get_current_user(credentials, store=_mongo_store)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "use_proxy": os.getenv("USE_PROXY", "1") != "0"}


# ---------- Authentication Endpoints ----------

@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await _mongo_store.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        user = await _mongo_store.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            name=user_data.name
        )
        
        # Create access token
        access_token = create_user_token(user)
        
        # Return token and user info
        return TokenResponse(
            access_token=access_token,
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                created_at=user["created_at"],
                is_active=user["is_active"]
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )


@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login and get JWT token"""
    try:
        # Get user by email
        user = await _mongo_store.get_user_by_email(credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = create_user_token(user)
        
        # Return token and user info
        return TokenResponse(
            access_token=access_token,
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                created_at=user["created_at"],
                is_active=user.get("is_active", True)
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to login: {str(e)}"
        )


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user_with_store)):
    """Get current user profile"""
    return current_user


# ---------- Session Management Endpoints ----------

@app.get("/sessions")
async def get_sessions(current_user: UserResponse = Depends(get_current_user_with_store)):
    """Get all sessions for current user"""
    try:
        sessions = await _mongo_store.get_user_sessions(current_user.id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"❌ Get sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@app.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Create a new chat session"""
    try:
        session = await _mongo_store.create_session(
            user_id=current_user.id,
            title=session_data.title or "New Chat"
        )
        return SessionResponse(**session)
    except Exception as e:
        print(f"❌ Create session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Delete a session"""
    try:
        # Verify session belongs to user
        session = await _mongo_store.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this session"
            )
        
        await _mongo_store.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


# ---------- Chat Endpoints (Updated with Authentication) ----------

@app.post("/chat")
async def chat(
    req: ChatRequest,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")
    
    try:
        # If no session_id provided, create a new session
        session_id = req.session_id
        if not session_id:
            session = await _mongo_store.create_session(
                user_id=current_user.id,
                title="New Chat"
            )
            session_id = session["id"]
        else:
            # Verify session belongs to user
            session = await _mongo_store.get_session_by_id(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            if session["user_id"] != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this session"
                )
        
        # Save user message with user_id
        await _mongo_store.save_chat_message_with_user(
            user_id=current_user.id,
            session_id=session_id,
            role="user",
            content=req.prompt
        )
        
        # Process with proxy
        proxy = _new_proxy(session_id=session_id)
        result = await proxy.handle_user_prompt_async(req.prompt)
        
        # Save assistant response with user_id
        await _mongo_store.save_chat_message_with_user(
            user_id=current_user.id,
            session_id=session_id,
            role="assistant",
            content=result.get("final_output", ""),
            agent_outputs=result
        )
        
        # Add session_id to response
        result["session_id"] = session_id
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process chat request: {str(e)}"
        )


@app.get("/history/{session_id}")
async def history(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    
    try:
        # Verify session belongs to user
        session = await _mongo_store.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        # Get history for this user's session
        history = await _mongo_store.get_session_history_for_user(
            user_id=current_user.id,
            session_id=session_id
        )
        
        return {
            "session_id": session_id,
            "history": history,
            "audit_logs": []
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ History error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch history: {str(e)}"
        )


@app.get("/replay/{session_id}")
async def replay(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    
    try:
        # Verify session belongs to user
        session = await _mongo_store.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        proxy = _new_proxy(session_id=session_id)
        data = await proxy.replay_session(session_id)
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Replay error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to replay session: {str(e)}"
        )


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
