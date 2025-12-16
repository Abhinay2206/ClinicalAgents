from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    """User model as stored in database"""
    id: str
    email: str
    name: str
    hashed_password: str
    created_at: str
    is_active: bool = True


class UserResponse(BaseModel):
    """User response (without password)"""
    id: str
    email: str
    name: str
    created_at: str
    is_active: bool = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SessionCreate(BaseModel):
    """Create a new chat session"""
    title: Optional[str] = "New Chat"


class SessionResponse(BaseModel):
    """Chat session response"""
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str


# Google OAuth Models
class GoogleAuthRequest(BaseModel):
    """Request model for Google OAuth authentication"""
    credential: str  # Google ID token from frontend
    

class GoogleAuthResponse(BaseModel):
    """Response model for Google OAuth authentication"""
    access_token: str
    user: UserResponse
