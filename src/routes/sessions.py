from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..models import Session as SessionModel
from ..db_models import SessionDB, WorkoutDB, SetDB, RepsDB
from ..database.database import get_db
from typing import List
from datetime import datetime

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionModel)
def create_session(session: SessionModel, db: Session = Depends(get_db)):
    # Create Reps, Sets, Workouts, Session in database
    db_session = SessionDB(
        user_id=session.user_id,
        started_at=session.started_at,
        finished_at=session.finished_at,
        notes=session.notes
    )
    
    for workout in session.workouts:
        db_workout = WorkoutDB(
            name=workout.name,
            started_at=workout.started_at,
            finished_at=workout.finished_at
        )
        db_session.workouts.append(db_workout)
        
        for set_ in workout.sets:
            db_set = SetDB(
                started_at=set_.started_at, 
                finished_at=set_.finished_at
            )
            db_rep = RepsDB(
                count=set_.reps.count, 
                intensity=set_.reps.intensity
            )
            
            # Set up the relationship properly
            db_set.reps = db_rep
            
            # Add both to the session
            db.add(db_rep)  # Add this line
            db_workout.sets.append(db_set)
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return session

@router.get("/{user_id}", response_model=List[SessionModel])
def get_sessions(user_id: int, db: Session = Depends(get_db)):
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