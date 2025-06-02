import re
import html
from typing import Optional
from datetime import datetime

def sanitize_string(input_str: str, max_length: int = 1000) -> str:
    """Sanitize string input to prevent injection attacks"""
    if not input_str:
        return ""
    
    # Truncate to max length
    sanitized = input_str[:max_length]
    
    # HTML escape to prevent XSS (good practice even for SQL)
    sanitized = html.escape(sanitized)
    
    # Remove null bytes (can cause issues in some databases)
    sanitized = sanitized.replace('\x00', '')
    
    # Remove potentially dangerous SQL patterns more aggressively
    dangerous_patterns = [
        r'(?i)\bdrop\s+table\b',
        r'(?i)\bdelete\s+from\b', 
        r'(?i)\binsert\s+into\b',
        r'(?i)\bupdate\s+.*\s+set\b',
        r'(?i)\bunion\s+select\b',
        r'(?i)\bselect\s+.*\s+from\b'
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '[BLOCKED]', sanitized)
    
    # Remove potentially dangerous characters
    sanitized = sanitized.replace(';', '').replace('--', '').replace('/*', '').replace('*/', '')
    
    return sanitized.strip()

def validate_workout_name(name: str) -> str:
    """Validate and sanitize workout names"""
    if not name or len(name.strip()) == 0:
        raise ValueError("Workout name cannot be empty")
    
    # Remove extra whitespace
    name = name.strip()
    
    # Check length
    if len(name) > 100:
        raise ValueError("Workout name too long (max 100 characters)")
    
    # Allow letters, numbers, spaces, hyphens, underscores, parentheses
    if not re.match(r'^[a-zA-Z0-9\s\-_()]+$', name):
        raise ValueError("Workout name contains invalid characters")
    
    return sanitize_string(name, max_length=100)

def validate_notes(notes: Optional[str]) -> Optional[str]:
    """Validate and sanitize session notes"""
    if not notes:
        return None
    
    notes = notes.strip()
    if len(notes) == 0:
        return None
    
    if len(notes) > 1000:
        raise ValueError("Notes too long (max 1000 characters)")
    
    return sanitize_string(notes, max_length=1000)

def validate_intensity(intensity: str) -> str:
    """Validate intensity level"""
    if not intensity:
        raise ValueError("Intensity cannot be empty")
    
    valid_intensities = ['low', 'medium', 'high']
    intensity_lower = intensity.lower().strip()
    
    if intensity_lower not in valid_intensities:
        raise ValueError(f"Invalid intensity '{intensity}'. Must be one of: {valid_intensities}")
    
    return intensity_lower

def validate_rep_count(count: int) -> int:
    """Validate rep count"""
    if not isinstance(count, int):
        raise ValueError("Rep count must be an integer")
    
    if count < 1:
        raise ValueError("Rep count must be at least 1")
    
    if count > 1000:
        raise ValueError("Rep count too high (max 1000)")
    
    return count

def validate_weight(weight: Optional[int]) -> Optional[int]:
    """Validate weight value"""
    if weight is None:
        return None
    
    if not isinstance(weight, int):
        raise ValueError("Weight must be an integer")
    
    if weight < 0:
        raise ValueError("Weight cannot be negative")
    
    if weight > 10000:
        raise ValueError("Weight too high (max 10000 lbs)")
    
    return weight

def validate_datetime(dt: datetime, field_name: str) -> datetime:
    """Validate datetime field"""
    if not isinstance(dt, datetime):
        raise ValueError(f"{field_name} must be a valid datetime")
    
    # Check if date is reasonable (not too far in past/future)
    # Handle both timezone-aware and timezone-naive datetimes
    if dt.tzinfo is not None:
        # Timezone-aware datetime - compare with UTC now
        from datetime import timezone
        now = datetime.now(timezone.utc)
        year_ago = now.replace(year=now.year - 1)
        year_ahead = now.replace(year=now.year + 1)
    else:
        # Timezone-naive datetime - compare with naive now
        now = datetime.now()
        year_ago = now.replace(year=now.year - 1)
        year_ahead = now.replace(year=now.year + 1)
    
    if dt < year_ago:
        raise ValueError(f"{field_name} cannot be more than a year in the past")
    
    if dt > year_ahead:
        raise ValueError(f"{field_name} cannot be more than a year in the future")
    
    return dt

def validate_time_order(start_time: datetime, end_time: datetime, context: str) -> None:
    """Validate that end time is after start time"""
    if end_time <= start_time:
        raise ValueError(f"{context} must finish after it starts")

def validate_session_limits(workouts_count: int, total_sets: int) -> None:
    """Validate session-level limits"""
    if workouts_count > 50:
        raise ValueError("Too many workouts in session (max 50)")
    
    if total_sets > 500:
        raise ValueError("Too many total sets in session (max 500)")

def validate_workout_limits(sets_count: int, workout_name: str) -> None:
    """Validate workout-level limits"""
    if sets_count > 100:
        raise ValueError(f"Too many sets in workout '{workout_name}' (max 100)")
    
    if sets_count < 1:
        raise ValueError(f"Workout '{workout_name}' must have at least one set")