from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..models import User as UserModel
from ..db_models import User as UserDB
from ..database.database import get_db
from bcrypt import hashpw, gensalt
from ..auth import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    generate_user_session_id
)
from ..models import UserLogin
from pydantic import BaseModel
import logging
import re
import os

# Create limiter for this module
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/users", tags=["users"])

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict  # Include safe user data in response

def validate_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username: str) -> bool:
    """Username validation - alphanumeric and underscore only"""
    pattern = r'^[a-z0-9_]{3,50}$'
    return re.match(pattern, username) is not None

@router.post("/", response_model=UserModel)
@limiter.limit("5/minute")
def create_user(request: Request, user: UserModel, db: Session = Depends(get_db)):
    logging.debug(f"Creating user: {user.model_dump()}")
    
    # Normalize username to lowercase for storage and comparison
    normalized_username = user.username.lower().strip()
    
    # Check if registration is disabled in production
    if os.getenv("ENVIRONMENT") == "production" and os.getenv("REGISTRATION_ENABLED") != "true":
        raise HTTPException(status_code=403, detail="Registration is currently disabled")
    
    # Additional validation
    if not validate_username(normalized_username):
        raise HTTPException(
            status_code=400, 
            detail="Username must be 3-50 characters, alphanumeric and underscore only"
        )
    
    if not validate_email(user.email):
        raise HTTPException(
            status_code=400, 
            detail="Invalid email format"
        )
    
    if len(user.password) < 8:
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 8 characters"
        )
    
    # Check if user already exists (case-insensitive check)
    existing_user = db.query(UserDB).filter(
        (func.lower(UserDB.username) == normalized_username) | 
        (func.lower(UserDB.email) == user.email.lower())
    ).first()
    
    if existing_user:
        if existing_user.username.lower() == normalized_username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = hashpw(user.password.encode("utf-8"), gensalt()).decode("utf-8")
    db_user = UserDB(
        username=normalized_username,
        email=user.email.lower(),
        password_hash=hashed_password
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    return user

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, user_credentials: UserLogin, db: Session = Depends(get_db)):
    print(f"DEBUG: Login attempt for username: {user_credentials.username}")
    
    # Normalize username for lookup (case-insensitive)
    normalized_username = user_credentials.username.lower().strip()
    
    # Case-insensitive username lookup
    user = db.query(UserDB).filter(
        func.lower(UserDB.username) == normalized_username
    ).first()
    
    if user:
        print(f"DEBUG: User found in DB: {user.username}")
        password_check = verify_password(user_credentials.password, user.password_hash)
        print(f"DEBUG: Password verification: {password_check}")
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        print("DEBUG: Login failed - invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    print("DEBUG: Creating tokens")
    
    # Generate a session ID for this login session
    session_id = generate_user_session_id()
    
    # Create token data with only username (no user_id)
    token_data = {
        "sub": user.username,  # Only include username
        "session_id": session_id  # For session tracking/invalidation
    }
    
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    # Return user data in response instead of embedding in token
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }
    
    print("DEBUG: Login successful")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_data
    )

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
def refresh_token(request: Request, refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        token_data = verify_refresh_token(refresh_request.refresh_token)
        
        # Verify user still exists
        user = db.query(UserDB).filter(
            UserDB.username == token_data["username"]
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens with same session ID
        new_token_data = {
            "sub": user.username,
            "session_id": token_data.get("session_id")
        }
        
        access_token = create_access_token(data=new_token_data)
        refresh_token = create_refresh_token(data=new_token_data)
        
        # Return user data
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
def logout(current_user: UserDB = Depends(get_current_user)):
    """Logout endpoint (for now just confirms valid token)"""
    # In a more sophisticated system, you'd invalidate the token server-side
    # For now, we just confirm the user is authenticated
    return {"message": "Successfully logged out"}

@router.get("/me")
def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at
    }