from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
import bcrypt  # Use bcrypt directly instead of passlib
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

from models import UserInDB, UserResponse

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "7"))

# HTTP Bearer token scheme
security = HTTPBearer()


import hashlib

def _pre_hash_password(password: str) -> str:
    """
    Pre-hash password with SHA-256 to handle bcrypt's 72-byte limit.
    This ensures we can support passwords of any length.
    """
    # SHA-256 produces a 32-byte digest (64 hex chars), which fits safely in bcrypt's 72-byte limit
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    # Pre-hash the plain password before verification
    pre_hashed = _pre_hash_password(plain_password)
    # Use bcrypt directly
    return bcrypt.checkpw(pre_hashed.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Pre-hash the password before passing to bcrypt
    pre_hashed = _pre_hash_password(password)
    # Use bcrypt directly to avoid passlib's strict validation
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    store=None  # Will be injected
) -> UserResponse:
    """
    Dependency to get the current authenticated user from JWT token.
    Usage: user = Depends(get_current_user)
    """
    token = credentials.credentials
    
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not available"
        )
    
    user = await store.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"],
        is_active=user.get("is_active", True)
    )


def create_user_token(user: dict) -> str:
    """Create a JWT token for a user"""
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"]}
    )
    return access_token
