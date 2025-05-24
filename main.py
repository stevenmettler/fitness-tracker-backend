from fastapi import FastAPI
from src.processor import add_workout
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from src.database.database import get_db, Base, engine
from src.routes import sessions, users

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

app.include_router(sessions.router)
app.include_router(users.router)

@app.get("/")
def root(db: Session = Depends(get_db)):
    return {"message": "Workout Tracker API"}


# app.include_router()
# @app.get("/sessions/{user_id}")
# async def root():
#     return add_workout()

# @app.post("/sessions")
# async def add_session():
#     return add_workout()

# @app.get("/sessions/{user_id}/workouts")
# async def get_workouts():
#     return add_workout()

# @app.post("/users")
# async def add_session():
#     return add_workout()

# @app.post("/users/login")
# async def add_session():
#     return add_workout()
