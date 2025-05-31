from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from .database.database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    
    # One user has many sessions
    sessions = relationship("SessionDB", back_populates="user", cascade="all, delete")

class SessionDB(Base):
    __tablename__ = "sessions"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=False)
    notes = Column(Text)
    
    # Belongs to one user
    user = relationship("User", back_populates="sessions")
    # One session has many workouts
    workouts = relationship("WorkoutDB", back_populates="session", cascade="all, delete")

class WorkoutDB(Base):
    __tablename__ = "workouts"
    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey("sessions.id"), nullable=False)
    name = Column(String(100), nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=False)
    
    # Belongs to one session
    session = relationship("SessionDB", back_populates="workouts")
    # One workout has many sets
    sets = relationship("SetDB", back_populates="workout", cascade="all, delete")

class SetDB(Base):
    __tablename__ = "sets"
    id = Column(BigInteger, primary_key=True)
    workout_id = Column(BigInteger, ForeignKey("workouts.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=False)
    
    # Belongs to one workout
    workout = relationship("WorkoutDB", back_populates="sets")
    # Each set has one rep object
    reps = relationship("RepsDB", back_populates="set", uselist=False, cascade="all, delete")

class RepsDB(Base):
    __tablename__ = "reps"
    id = Column(BigInteger, primary_key=True)
    set_id = Column(BigInteger, ForeignKey("sets.id"), nullable=False)
    count = Column(Integer, nullable=False)
    intensity = Column(String(20), nullable=False)
    weight = Column(Integer, nullable=False)
    
    # Belongs to one set
    set = relationship("SetDB", back_populates="reps")