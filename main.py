from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database.database import get_db, Base, engine
from src.routes import sessions, users
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Fitness Tracker API", version="1.0.0")

# Add CORS middleware - ADD THIS SECTION
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # In case React runs on 3001
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create database tables (only in development)
if os.getenv("ENVIRONMENT") != "production":
    Base.metadata.create_all(bind=engine)

app.include_router(sessions.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Fitness Tracker API", "status": "healthy"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}