from pydantic import BaseModel, EmailStr, validator, ValidationError
from typing import List, Union, Optional
from datetime import datetime
import json

class User(BaseModel):
    username: str
    email: EmailStr
    password: str

class Reps(BaseModel):
    intensity: str
    count: int

    @validator("count")
    def check_at_least_one_rep(cls, v):
        if v < 1:
            raise ValueError("At lease one rep is required in a set")
        return v

class Set(BaseModel):
    reps: Reps
    started_at: datetime
    finished_at: datetime

    @validator("finished_at")
    def check_finished_after_started(cls, v, values):
        if "started_at" in values and v <= values["started_at"]:
            raise ValueError("finished_at must be after started_at")
        return v

class Workout(BaseModel):
    sets: List[Set]
    name: str
    started_at: datetime
    finished_at: datetime

    @validator("finished_at")
    def check_finished_after_started(cls, v, values):
        if "started_at" in values and v <= values["started_at"]:
            raise ValueError("finished_at must be after started_at")
        return v

    @validator("sets")
    def check_at_least_one_set(cls, v):
        if len(v) < 1:
            raise ValueError("At least one set is required in a workout")
        return v

class Session(BaseModel):
    user_id: int
    workouts: List[Workout]
    started_at: datetime
    finished_at: datetime
    notes: Optional[str]

    @validator("finished_at")
    def check_finished_after_started(cls, v, values):
        if "started_at" in values and v <= values["started_at"]:
            raise ValueError("finished_at must be after started_at")
        return v

    @validator("workouts")
    def check_at_least_one_workout(cls, v):
        if len(v) < 1:
            raise ValueError("At least one workout is required in a session")
        return v

class User(BaseModel):
    username: str
    email: str
    password: str

def create_session(json_input: Union[str, bytes, bytearray, dict]) -> Session:
    from pydantic import ValidationError
    try:
        # Handle dictionary input (from import_json)
        if isinstance(json_input, dict):
            data = json_input
        # Handle file path
        elif isinstance(json_input, str) and json_input.endswith('.json'):
            with open(json_input, 'r') as file:
                json_data = file.read()
            data = json.loads(json_data)
        # Handle JSON string
        else:
            print(f"\n\n\n\nWE ARE HERE\n\n\n\n")
            data = json.loads(json_input)

        # Validate and create Session object
        session = Session(**data["session"])
        return session
    except ValidationError as e:
        raise ValueError(f"Invalid session data: {e}")
    except KeyError as e:
        raise ValueError("JSON must contain a 'session' key")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except FileNotFoundError:
        raise ValueError(f"File not found: {json_input}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred: {e}")
