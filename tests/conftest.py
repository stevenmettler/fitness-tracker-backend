import pytest
from datetime import datetime, timedelta

@pytest.fixture
def sample_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com", 
        "password": "password123"
    }

@pytest.fixture
def auth_headers(client, sample_user_data):
    # Register user
    register_response = client.post("/users/", json=sample_user_data)
    print(f"Register response: {register_response.status_code}, {register_response.text}")
    
    # Login
    login_response = client.post("/users/login", json={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"]
    })
    print(f"Login response: {login_response.status_code}, {login_response.text}")
    
    if login_response.status_code != 200:
        pytest.fail(f"Login failed: {login_response.text}")
    
    response_data = login_response.json()
    if "access_token" not in response_data:
        pytest.fail(f"No access_token in response: {response_data}")
        
    token = response_data["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def valid_session_data():
    now = datetime.now()
    return {
        "user_id": 1,
        "started_at": now.isoformat() + "Z",
        "finished_at": (now + timedelta(hours=1)).isoformat() + "Z", 
        "notes": "Test session",
        "workouts": [
            {
                "name": "Bench Press",
                "started_at": now.isoformat() + "Z",
                "finished_at": (now + timedelta(minutes=30)).isoformat() + "Z",
                "sets": [
                    {
                        "started_at": now.isoformat() + "Z",
                        "finished_at": (now + timedelta(minutes=5)).isoformat() + "Z",
                        "reps": {
                            "count": 10,
                            "intensity": "medium",
                            "weight": 135
                        }
                    }
                ]
            }
        ]
    }