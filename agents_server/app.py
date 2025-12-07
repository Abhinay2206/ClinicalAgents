from __future__ import annotations

import os
from typing import Optional, Dict, Any, List
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


class EnrollmentPredictionRequest(BaseModel):
    disease: str
    criteria_text: Optional[str] = ""
    phase: int = 2
    target_enrollment: int = 100
    site_count: int = 5
    recruitment_duration: int = 12


class EnrollmentPredictionResponse(BaseModel):
    predicted_class: str
    confidence_scores: Dict[str, float]
    top_risk_drivers: List[Dict[str, Any]]
    error: Optional[str] = None


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
_ml_predictor: Optional[Any] = None


@app.on_event("startup")
async def startup_event():
    """Initialize expensive resources once at startup"""
    global _llm_client, _mongo_store, _orchestrator, _ml_predictor
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
    
    # Initialize ML predictor (optional - may not have model yet)
    try:
        from ml_models.inference import EnrollmentPredictor
        _ml_predictor = EnrollmentPredictor()
        print("✓ ML Enrollment Predictor initialized")
    except FileNotFoundError:
        print("⚠️ ML model not found - prediction endpoint will return error until model is trained")
        _ml_predictor = None
    except Exception as e:
        print(f"⚠️ ML predictor initialization failed: {e}")
        _ml_predictor = None
    
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


class SessionUpdate(BaseModel):
    title: str


@app.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    update_data: SessionUpdate,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Update a session (e.g., title)"""
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
                detail="Not authorized to update this session"
            )
        
        # Update session title
        success = await _mongo_store.update_session_title(session_id, update_data.title)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update session"
            )
        
        # Return updated session
        updated_session = await _mongo_store.get_session_by_id(session_id)
        return SessionResponse(**updated_session)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
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
        
        # Process with proxy (pass user_id for memory integration)
        proxy = _new_proxy(session_id=session_id)
        result = await proxy.handle_user_prompt_async(req.prompt, user_id=current_user.id)
        
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


# ---------- Feedback Endpoints ----------

class FeedbackSubmit(BaseModel):
    message_id: str
    feedback_type: str  # "thumbs_up", "thumbs_down", "correction", "rating"
    rating: Optional[int] = None  # 1-5 for rating type
    correction_text: Optional[str] = None  # For correction type
    comment: Optional[str] = None


@app.post("/feedback")
async def submit_feedback(
    feedback: FeedbackSubmit,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Submit feedback on an agent response"""
    try:
        from feedback_manager import FeedbackManager
        
        feedback_manager = FeedbackManager(store=_mongo_store, llm=_llm_client)
        
        # Get message to find session_id
        message = await _mongo_store.get_message_by_id(feedback.message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        session_id = message.get("session_id")
        
        # Verify session belongs to user
        session = await _mongo_store.get_session_by_id(session_id)
        if not session or session["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to provide feedback on this message"
            )
        
        # Collect feedback
        feedback_data = {
            "rating": feedback.rating,
            "correction_text": feedback.correction_text,
            "comment": feedback.comment
        }
        
        feedback_id = await feedback_manager.collect_feedback(
            session_id=session_id,
            user_id=current_user.id,
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type,
            feedback_data=feedback_data
        )
        
        return {
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Feedback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@app.get("/feedback/{session_id}")
async def get_feedback(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Get feedback history for a session"""
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
        
        feedback = await _mongo_store.get_session_feedback(session_id)
        return {"feedback": feedback}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get feedback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}"
        )


# ---------- Memory Endpoints ----------

@app.get("/memory/{session_id}")
async def get_memory(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Get memory state for a session"""
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
        
        memory_states = await _mongo_store.get_memory_state(session_id, limit=20)
        summary = await _mongo_store.get_conversation_summary(session_id)
        
        return {
            "memory_states": memory_states,
            "summary": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get memory error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory: {str(e)}"
        )


@app.post("/memory/clear/{session_id}")
async def clear_memory(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Clear memory for a session"""
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
                detail="Not authorized to modify this session"
            )
        
        success = await _mongo_store.clear_memory_state(session_id)
        
        return {
            "success": success,
            "message": "Memory cleared successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Clear memory error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear memory: {str(e)}"
        )


# ---------- Preferences Endpoints ----------

class PreferencesUpdate(BaseModel):
    response_style: Optional[str] = None  # "technical", "simple", "balanced"
    preferred_agents: Optional[List[str]] = None
    excluded_topics: Optional[List[str]] = None
    language_level: Optional[str] = None  # "expert", "intermediate", "beginner"


@app.get("/preferences")
async def get_preferences(current_user: UserResponse = Depends(get_current_user_with_store)):
    """Get user preferences"""
    try:
        preferences = await _mongo_store.get_user_preferences(current_user.id)
        
        if not preferences:
            # Return default preferences
            return {
                "preferences": {
                    "response_style": "balanced",
                    "preferred_agents": [],
                    "excluded_topics": [],
                    "language_level": "intermediate"
                }
            }
        
        return preferences
    except Exception as e:
        print(f"❌ Get preferences error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )


@app.put("/preferences")
async def update_preferences(
    prefs: PreferencesUpdate,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Update user preferences"""
    try:
        # Build preferences dict from non-None values
        preferences = {}
        if prefs.response_style is not None:
            preferences["response_style"] = prefs.response_style
        if prefs.preferred_agents is not None:
            preferences["preferred_agents"] = prefs.preferred_agents
        if prefs.excluded_topics is not None:
            preferences["excluded_topics"] = prefs.excluded_topics
        if prefs.language_level is not None:
            preferences["language_level"] = prefs.language_level
        
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No preferences provided"
            )
        
        # Get existing preferences and merge
        existing = await _mongo_store.get_user_preferences(current_user.id)
        if existing and "preferences" in existing:
            existing["preferences"].update(preferences)
            preferences = existing["preferences"]
        
        success = await _mongo_store.update_user_preferences(current_user.id, preferences)
        
        return {
            "success": success,
            "preferences": preferences
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update preferences error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )


# ---------- ML Prediction Endpoint ----------

@app.post("/api/predict-enrollment", response_model=EnrollmentPredictionResponse)
async def predict_enrollment(req: EnrollmentPredictionRequest):
    """
    Predict enrollment outcome for a clinical trial using ML model.
    Public endpoint - no authentication required.
    """
    try:
        # Check if ML predictor is available
        if _ml_predictor is None:
            return EnrollmentPredictionResponse(
                predicted_class="error",
                confidence_scores={},
                top_risk_drivers=[],
                error="ML model not available. Please ensure enrollment_model.pt is in ml_models/saved_models/"
            )
        
        # Prepare tabular features
        tabular_features = {
            'phase': req.phase,
            'target_enrollment': req.target_enrollment,
            'site_count': req.site_count,
            'recruitment_duration': req.recruitment_duration
        }
        
        # Make prediction
        result = _ml_predictor.predict_enrollment(
            disease=req.disease,
            criteria_text=req.criteria_text,
            tabular_features=tabular_features
        )
        
        return EnrollmentPredictionResponse(
            predicted_class=result['predicted_class'],
            confidence_scores=result['confidence_scores'],
            top_risk_drivers=result['top_risk_drivers']
        )
    
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        return EnrollmentPredictionResponse(
            predicted_class="error",
            confidence_scores={},
            top_risk_drivers=[],
            error=f"Prediction failed: {str(e)}"
        )


# ---------- Clinical Trials Search Endpoint ----------

@app.get("/api/trials")
async def search_trials(disease: str, limit: int = 50):
    """
    Search clinical trials by disease name from CSV.
    Public endpoint - no authentication required.
    """
    try:
        import pandas as pd
        import numpy as np
        import os
        
        # Path to clinical trials CSV
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, 'datasets', 'clinical_trials.csv')
        
        if not os.path.exists(csv_path):
            raise HTTPException(
                status_code=404,
                detail="Clinical trials database not found"
            )
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Case-insensitive search in Disease column
        mask = df['Disease'].str.contains(disease, case=False, na=False)
        results = df[mask].head(limit)
        
        # Replace NaN values with None for JSON serialization
        results = results.replace({np.nan: None})
        
        # Convert to list of dicts
        trials = results.to_dict('records')
        
        return {
            "disease": disease,
            "count": len(trials),
            "trials": trials
        }
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Clinical trials database not found"
        )
    except Exception as e:
        print(f"❌ Trials search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search trials: {str(e)}"
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
