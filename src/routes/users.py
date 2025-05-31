from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..models import User as UserModel
from ..db_models import User as UserDB
from ..database.database import get_db
from bcrypt import hashpw, gensalt
from ..auth import verify_password, create_access_token
from ..models import UserLogin
import logging
import re
import os

# Create limiter for this module
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/users", tags=["users"])

def validate_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username: str) -> bool:
    """Username validation - alphanumeric and underscore only"""
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    return re.match(pattern, username) is not None

@router.post("/", response_model=UserModel)
@limiter.limit("5/minute")  # Only 5 registrations per minute per IP
def create_user(request: Request, user: UserModel, db: Session = Depends(get_db)):
    logging.debug(f"Creating user: {user.model_dump()}")
    
    # Check if registration is disabled in production
    if os.getenv("ENVIRONMENT") == "production" and os.getenv("REGISTRATION_ENABLED") != "true":
        raise HTTPException(status_code=403, detail="Registration is currently disabled")
    
    # Additional validation
    if not validate_username(user.username):
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
    
    # Check if user already exists
    existing_user = db.query(UserDB).filter(
        (UserDB.username == user.username) | (UserDB.email == user.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = hashpw(user.password.encode("utf-8"), gensalt()).decode("utf-8")
    db_user = UserDB(
        username=user.username,
        email=user.email,
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

@router.post("/login")
@limiter.limit("10/minute")  # 10 login attempts per minute per IP
def login(request: Request, user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}