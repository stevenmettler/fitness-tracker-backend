from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import User as UserModel
from ..db_models import User as UserDB
from ..database.database import get_db
from bcrypt import hashpw, gensalt
import logging


router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserModel)
def create_user(user: UserModel, db: Session = Depends(get_db)):
    logging.debug(f"Creating user: {user.model_dump()}")
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
        raise HTTPException(status_code=400, detail="Username or email already exists")
    return user