from pydantic import BaseModel, EmailStr, field_validator, model_validator, ValidationError, Field
from typing import List, Union, Optional
from datetime import datetime
import json
from .validation.validation import (
    validate_workout_name, 
    validate_notes, 
    validate_intensity,
    validate_rep_count,
    validate_weight,
    validate_datetime,
    validate_time_order
)

class User(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class Reps(BaseModel):
    intensity: str
    count: int
    weight: Optional[int] = None

    @field_validator("intensity")
    @classmethod
    def validate_intensity_level(cls, v):
        return validate_intensity(v)
    
    @field_validator("count")
    @classmethod
    def validate_rep_count_field(cls, v):
        return validate_rep_count(v)
    
    @field_validator("weight")
    @classmethod
    def validate_weight_field(cls, v):
        return validate_weight(v)

class Set(BaseModel):
    reps: Reps
    started_at: datetime
    finished_at: datetime

    @field_validator("started_at")
    @classmethod
    def validate_started_at(cls, v):
        return validate_datetime(v, "Set start time")
    
    @field_validator("finished_at")
    @classmethod
    def validate_finished_at(cls, v):
        return validate_datetime(v, "Set end time")

    @model_validator(mode='after')
    def check_finished_after_started(self):
        validate_time_order(self.started_at, self.finished_at, "Set")
        return self

class Workout(BaseModel):
    sets: List[Set]
    name: str
    started_at: datetime
    finished_at: datetime

    @field_validator("name")
    @classmethod
    def validate_workout_name_field(cls, v):
        return validate_workout_name(v)
    
    @field_validator("started_at")
    @classmethod
    def validate_workout_started_at(cls, v):
        return validate_datetime(v, "Workout start time")
    
    @field_validator("finished_at")
    @classmethod
    def validate_workout_finished_at(cls, v):
        return validate_datetime(v, "Workout end time")

    @field_validator("sets")
    @classmethod
    def check_at_least_one_set(cls, v):
        if len(v) < 1:
            raise ValueError("At least one set is required in a workout")
        if len(v) > 100:
            raise ValueError("Too many sets in workout (max 100)")
        return v

    @model_validator(mode='after')
    def check_finished_after_started(self):
        validate_time_order(self.started_at, self.finished_at, "Workout")
        return self

class Session(BaseModel):
    # user_id: int  # REMOVE this line entirely - backend gets user from JWT
    workouts: List[Workout]
    started_at: datetime
    finished_at: datetime
    notes: Optional[str] = None

    @field_validator("started_at")
    @classmethod
    def validate_session_started_at(cls, v):
        return validate_datetime(v, "Session start time")
    
    @field_validator("finished_at")
    @classmethod
    def validate_session_finished_at(cls, v):
        return validate_datetime(v, "Session end time")

    @field_validator("workouts")
    @classmethod
    def check_at_least_one_workout(cls, v):
        if len(v) < 1:
            raise ValueError("At least one workout is required in a session")
        if len(v) > 50:
            raise ValueError("Too many workouts in session (max 50)")
        
        # Check total sets across all workouts
        total_sets = sum(len(workout.sets) for workout in v)
        if total_sets > 500:
            raise ValueError("Too many total sets in session (max 500)")
        
        return v
    
    @field_validator("notes")
    @classmethod
    def validate_session_notes(cls, v):
        return validate_notes(v)

    @model_validator(mode='after')
    def check_finished_after_started(self):
        validate_time_order(self.started_at, self.finished_at, "Session")
        return self

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