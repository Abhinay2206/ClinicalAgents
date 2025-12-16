from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

from models import UserInDB, UserResponse

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    return pwd_context.verify(pre_hashed, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Pre-hash the password before passing to bcrypt
    pre_hashed = _pre_hash_password(password)
    return pwd_context.hash(pre_hashed)


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


async def verify_google_token(credential: str) -> dict:
    """
    Verify Google OAuth ID token and extract user information.
    
    Args:
        credential: Google ID token from frontend
        
    Returns:
        dict with user info: email, name, picture, sub (Google user ID)
        
    Raises:
        HTTPException if token is invalid
    """
    try:
        import httpx
        from jose import jwt
        
        # Get Google's public keys
        async with httpx.AsyncClient() as client:
            # First decode without verification to get kid (key id)
            unverified_header = jwt.get_unverified_header(credential)
            
            # Get Google's public keys
            keys_response = await client.get("https://www.googleapis.com/oauth2/v3/certs")
            keys = keys_response.json()["keys"]
            
            # Find the right key
            key = None
            for k in keys:
                if k["kid"] == unverified_header["kid"]:
                    key = k
                    break
            
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: key not found"
                )
            
            # Verify and decode the token
            # Google ID tokens are JWTs signed with RS256
            from jose.backends import RSAKey
            rsa_key = RSAKey(key, algorithm="RS256")
            
            # Decode and verify
            payload = jwt.decode(
                credential,
                rsa_key,
                algorithms=["RS256"],
                audience=os.getenv("GOOGLE_CLIENT_ID")
            )
            
            # Extract user info
            user_info = {
                "email": payload.get("email"),
                "name": payload.get("name"),
                "picture": payload.get("picture"),
                "sub": payload.get("sub"),  # Google user ID
                "email_verified": payload.get("email_verified", False)
            }
            
            # Ensure email is verified
            if not user_info["email_verified"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email not verified by Google"
                )
            
            return user_info
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Google token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to verify Google token: {str(e)}"
        )

