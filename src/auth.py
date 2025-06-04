from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database.database import get_db
from .db_models import User
import os
import secrets

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_user_session_id():
    """Generate a secure random session ID for the user"""
    return secrets.token_urlsafe(32)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token with only username and session ID - NO user_id"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Only include non-sensitive data in JWT
    secure_payload = {
        "sub": to_encode["sub"],  # username only
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    # Add session ID if provided (for tracking/invalidation)
    if "session_id" in to_encode:
        secure_payload["session_id"] = to_encode["session_id"]
    
    return jwt.encode(secure_payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """Create a refresh token with longer expiration"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    secure_payload = {
        "sub": to_encode["sub"],  # username only
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    
    if "session_id" in to_encode:
        secure_payload["session_id"] = to_encode["session_id"]
    
    return jwt.encode(secure_payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_refresh_token(token: str):
    """Verify refresh token and return user data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return {
            "username": username,
            "session_id": payload.get("session_id")
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token (without exposing user_id in token)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type = payload.get("type", "access")
        
        # Reject refresh tokens in regular auth
        if token_type == "refresh":
            raise credentials_exception
            
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Look up user by username only (no user_id in token)
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_user_id(current_user: User = Depends(get_current_user)) -> int:
    """Helper function to get user ID after authentication"""
    return current_user.id