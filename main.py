from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from src.database.database import get_db, Base, engine
from src.routes import sessions, users
import os

app = FastAPI(title="Fitness Tracker API", version="1.0.0")

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
        # Simple database connectivity test
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}