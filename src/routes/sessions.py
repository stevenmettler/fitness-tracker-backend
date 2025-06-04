from fastapi import Request, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..models import Session as SessionModel
from ..db_models import SessionDB, WorkoutDB, SetDB, RepsDB, User
from ..database.database import get_db
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..auth import get_current_user  # This now returns User object, not user_id
from ..validation.validation import (
    validate_workout_name,
    validate_notes,
    validate_intensity,
    validate_rep_count,
    validate_weight,
    validate_session_limits,
    validate_workout_limits
)
from typing import List
from datetime import datetime
import logging

# Create limiter for this module
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionModel)
@limiter.limit("10/minute") 
def create_session(
    request: Request, 
    session: SessionModel, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # This is now a User object
):
    try:
        # Additional server-side validation (Pydantic already validated, but extra safety)
        total_sets = sum(len(workout.sets) for workout in session.workouts)
        validate_session_limits(len(session.workouts), total_sets)
        
        # Create session with authenticated user's ID (from User object, not JWT)
        db_session = SessionDB(
            user_id=current_user.id,  # Get ID from authenticated User object
            started_at=session.started_at,
            finished_at=session.finished_at,
            notes=validate_notes(session.notes)  # Sanitize notes
        )
        
        for workout in session.workouts:
            # Validate and sanitize workout data
            sanitized_name = validate_workout_name(workout.name)
            validate_workout_limits(len(workout.sets), sanitized_name)
            
            db_workout = WorkoutDB(
                name=sanitized_name,
                started_at=workout.started_at,
                finished_at=workout.finished_at
            )
            db_session.workouts.append(db_workout)
            
            for set_ in workout.sets:
                # Additional validation for sets (double-check after Pydantic)
                validated_count = validate_rep_count(set_.reps.count)
                validated_weight = validate_weight(set_.reps.weight)
                validated_intensity = validate_intensity(set_.reps.intensity)
                
                db_set = SetDB(
                    started_at=set_.started_at, 
                    finished_at=set_.finished_at
                )
                
                db_rep = RepsDB(
                    count=validated_count,
                    intensity=validated_intensity,
                    weight=validated_weight
                )
                
                # Set up the relationship properly
                db_set.reps = db_rep
                
                # Add both to the session
                db.add(db_rep)
                db_workout.sets.append(db_set)
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        logging.info(f"Session created successfully for user {current_user.username} (ID: {current_user.id}) with {len(session.workouts)} workouts")
        return session
        
    except ValueError as ve:
        logging.warning(f"Validation error in session creation for user {current_user.username}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating session for user {current_user.username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/", response_model=List[SessionModel])
def get_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # User object
):
    """Get all sessions for the authenticated user"""
    sessions = db.query(SessionDB)\
        .options(
            joinedload(SessionDB.workouts)
            .joinedload(WorkoutDB.sets)
            .joinedload(SetDB.reps)
        )\
        .filter(SessionDB.user_id == current_user.id)\
        .all()
    
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions found")
    return sessions

@router.get("/{user_id}", response_model=List[SessionModel])
def get_sessions(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # User object
):
    """Get sessions for a specific user (only if it's the authenticated user)"""
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Cannot access another user's sessions"
        )
    
    sessions = db.query(SessionDB)\
        .options(
            joinedload(SessionDB.workouts)
            .joinedload(WorkoutDB.sets)
            .joinedload(SetDB.reps)
        )\
        .filter(SessionDB.user_id == user_id)\
        .all()
    
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions found")
    return sessions