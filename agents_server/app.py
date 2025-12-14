from __future__ import annotations

import os
from typing import Optional, Dict, Any, List
from functools import wraps

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from llm_client import GrokClient
from storage.mongo_async import AsyncMongoStore
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
app = FastAPI(title="ClinicalAgents API - v2.0", version="2.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global singletons for performance - initialized once at startup
_llm_client: Optional[GrokClient] = None
_mongo_store: Optional[AsyncMongoStore] = None
_ml_predictor: Optional[Any] = None


@app.on_event("startup")
async def startup_event():
    """Initialize expensive resources once at startup"""
    global _llm_client, _mongo_store, _ml_predictor
    print("🚀 Initializing ClinicalAgent 2.0...")
    
    # Initialize LLM client (lightweight)
    _llm_client = GrokClient()
    print("✓ LLM client initialized")
    
    # Initialize MongoDB store (connection pool)
    _mongo_store = AsyncMongoStore()
    print("✓ MongoDB store initialized")
    
    # Verify LangGraph v2 availability
    try:
        from langgraph_v2.config import Config
        Config.print_status()
        print("✓ ClinicalAgent 2.0 LangGraph workflow ready")
    except Exception as e:
        print(f"⚠️ LangGraph v2 check failed: {e}")
    
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


# ---------- Chat Endpoints (ClinicalAgent 2.0) ----------

@app.post("/chat")
async def chat(
    req: ChatRequest,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """
    Main chat endpoint - Uses ClinicalAgent 2.0 LangGraph workflow
    
    NOW WITH CONVERSATIONAL CONTEXT:
    - Detects follow-up queries and resolves references
    - Enriches queries with conversation history
    - Maintains memory state for ChatGPT-like conversations
    
    Supports both:
    - Numbered format for trial predictions: (1) drug: ... (2) disease: ...
    - General clinical trial questions
    - Follow-up queries: "What about its efficacy?"
    - Refinements: "Can you give more details?"
    """
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
        
        # ===== NEW: CONVERSATIONAL CONTEXT PROCESSING =====
        from memory_manager import MemoryManager
        from feedback_manager import FeedbackManager
        
        # Initialize managers
        memory_mgr = MemoryManager(store=_mongo_store, llm=_llm_client)
        feedback_mgr = FeedbackManager(store=_mongo_store, llm=_llm_client)
        
        # Load conversation history and memory state
        conversation_history = await _mongo_store.get_session_history_for_user(
            user_id=current_user.id,
            session_id=session_id
        )
        
        # Get enhanced conversation context
        memory_state = await memory_mgr.get_conversation_context(
            session_id=session_id,
            current_query=req.prompt,
            include_last_response=True
        )
        
        # Check if this is a conversational follow-up
        is_followup = feedback_mgr.is_conversational_followup(req.prompt)
        
        # Process query (original or enriched)
        query_to_process = req.prompt
        followup_info = None
        
        if is_followup and conversation_history:
            print(f"🔄 Detected follow-up query: {req.prompt}")
            
            # Process as follow-up with context
            followup_info = await feedback_mgr.process_followup(
                query=req.prompt,
                session_id=session_id,
                user_id=current_user.id,
                conversation_history=conversation_history,
                memory_state=memory_state
            )
            
            # Use enriched query for processing
            query_to_process = followup_info['enriched_query']
            
            print(f"✨ Enriched query: {query_to_process}")
        
        # Save user message (original query)
        await _mongo_store.save_chat_message_with_user(
            user_id=current_user.id,
            session_id=session_id,
            role="user",
            content=req.prompt
        )
        
        # ===== EXISTING: QUERY PROCESSING =====
        # Check if this is a trial prediction request (multiple formats supported)
        import re
        from trial_input_parser import parse_trial_input, format_to_numbered
        
        # Try numbered format first (existing format)
        is_numbered_format = bool(re.search(r'\(1\)\s*drug:', query_to_process, re.IGNORECASE))
        
        if is_numbered_format:
            # Use prompt as-is for numbered format
            trial_input = query_to_process
            is_trial_prediction = True
        else:
            # Try parsing natural language format
            parsed_trial = parse_trial_input(query_to_process)
            if parsed_trial:
                # Convert to numbered format for workflow
                trial_input = format_to_numbered(parsed_trial)
                is_trial_prediction = True
            else:
                is_trial_prediction = False
                trial_input = None
        
        if is_trial_prediction:
            # Use LangGraph v2 workflow for trial predictions
            from langgraph_v2.workflow import ClinicalTrialWorkflow
            
            print("\n" + "="*60)
            print("🚀 Starting ClinicalAgent 2.0 Workflow")
            if followup_info:
                print(f"📝 Context-enriched: {followup_info['is_followup']}")
            print("="*60)
            
            workflow = ClinicalTrialWorkflow(verbose=True)
            prediction_result = workflow.predict(trial_input)
            
            # Format response with FULL agent reports for proper UI rendering
            final_output = f"""🎯 Clinical Trial Prediction

**Prediction**: {prediction_result['prediction']}  
**Confidence**: {int(prediction_result['confidence'] * 100)}%

---

## 📊 Step-by-Step Analysis

{prediction_result['reasoning']}

---

**Agent Reports:**

**Enrollment**: {prediction_result['reports']['enrollment'] or 'No enrollment report available'}

**Safety**: {prediction_result['reports']['safety'] or 'No safety report available'}

**Efficacy**: {prediction_result['reports']['efficacy'] or 'No efficacy report available'}
"""
            
            # Convert followup_info context to dict for MongoDB
            serializable_followup_info = None
            if followup_info:
                serializable_followup_info = {
                    **followup_info,
                    'context': followup_info['context'].to_dict() if followup_info.get('context') else None
                }
            
            result = {
                "final_output": final_output,
                "session_id": session_id,
                "prediction": prediction_result['prediction'],
                "confidence": prediction_result['confidence'],
                "activated_agents": ["ClinicalAgent 2.0"],
                "status": "success",
                "agent_results": prediction_result,
                "context_used": is_followup,
                "followup_info": serializable_followup_info
            }
        else:
            # For general questions, use context-aware LLM response
            # If follow-up, include context in prompt
            if is_followup and memory_state.get('last_response'):
                context_prompt = f"""You are a helpful clinical trial assistant. 

Previous context:
User asked: {memory_state.get('last_query', '')[:200]}
You responded: {memory_state.get('last_response', '')[:500]}

Current question: {query_to_process}

Provide a helpful answer that builds on the previous context."""
            else:
                context_prompt = f"You are a helpful clinical trial assistant. Answer this question: {query_to_process}"
            
            
            response = _llm_client.generate(
                context_prompt,
                max_tokens=2000,  # Increased from 500 to allow complete clinical responses
                temperature=0.7
            )
            
            # Convert followup_info context to dict for MongoDB
            serializable_followup_info = None
            if followup_info:
                serializable_followup_info = {
                    **followup_info,
                    'context': followup_info['context'].to_dict() if followup_info.get('context') else None
                }
            
            result = {
                "final_output": response,
                "session_id": session_id,
                "activated_agents": ["General LLM"],
                "status": "success",
                "context_used": is_followup,
                "followup_info": serializable_followup_info
            }
        
        # Save assistant response with context metadata
        await _mongo_store.save_chat_message_with_user(
            user_id=current_user.id,
            session_id=session_id,
            role="assistant",
            content=result["final_output"],
            agent_outputs=result
        )
        
        # ===== NEW: UPDATE MEMORY STATE =====
        # Store this conversation turn in memory with enhanced metadata
        await memory_mgr.add_conversation_turn(
            session_id=session_id,
            user_id=current_user.id,
            user_query=req.prompt,
            agent_response=result["final_output"],
            activated_agents=result.get("activated_agents", []),
            metadata={
                "is_followup": is_followup,
                "context_used": is_followup,
                "topics": memory_mgr.track_topics(req.prompt + " " + result["final_output"])
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process chat request: {str(e)}"
        )






@app.get("/history/{session_id}")
async def history(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """Get conversation history for a session"""
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


# ---------- ClinicalAgent 2.0 Endpoints ----------

class ClinicalTrialV2Request(BaseModel):
    """Request model for ClinicalAgent 2.0 predictions"""
    input_text: str  # Numbered format: (1) drug: ... (2) disease: ...
    verbose: Optional[bool] = False


class ClinicalTrialV2Response(BaseModel):
    """Response model for ClinicalAgent 2.0 predictions"""
    prediction: str  # PASS or FAIL
    confidence: float  # 0.0 to 1.0
    reasoning: str  # Chain-of-thought explanation
    reports: Dict[str, Optional[str]]  # Individual agent reports
    drug_parsed: Dict[str, Optional[str]]  # Original and cleaned drug name
    disease_parsed: Optional[str]  # Extracted disease name
    warnings: List[str]  # Non-critical issues
    errors: List[str]  # Critical errors


@app.post("/api/v2/clinical-trial", response_model=ClinicalTrialV2Response)
async def predict_clinical_trial_v2(
    req: ClinicalTrialV2Request,
    current_user: UserResponse = Depends(get_current_user_with_store)
):
    """
    Predict clinical trial outcome using ClinicalAgent 2.0 LangGraph workflow
    
    **Input Format**:
    ```
    Features contain (1) drug: <drug_name>; (2) disease: <disease_name>; 
    (3) inclusion criteria: <criteria>; (4) exclusion criteria: <criteria>;
    ```
    
    **Example**:
    ```json
    {
        "input_text": "(1) drug: Metformin tablet; (2) disease: Type 2 Diabetes; (3) inclusion criteria: Adults 18-65; (4) exclusion criteria: Kidney disease;"
    }
    ```
    
    **Returns**: PASS/FAIL prediction with confidence score and detailed agent reports
    """
    try:
        from langgraph_v2.workflow import ClinicalTrialWorkflow
        
        # Create workflow instance
        workflow = ClinicalTrialWorkflow(verbose=req.verbose)
        
        # Run prediction
        result = workflow.predict(req.input_text)
        
        # Log to MongoDB for tracking
        await _mongo_store.log_event(
            session_id=f"v2_{current_user.id}",
            event="clinical_trial_prediction_v2",
            agent_name="LangGraphWorkflow",
            content={
                "user_id": current_user.id,
                "input": req.input_text,
                "prediction": result['prediction'],
                "confidence": result['confidence']
            },
            status="success"
        )
        
        return ClinicalTrialV2Response(**result)
        
    except Exception as e:
        print(f"❌ ClinicalAgent 2.0 error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process clinical trial prediction: {str(e)}"
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
