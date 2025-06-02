import pytest

class TestSessionsAPI:
    def test_create_valid_session(self, client, auth_headers, valid_session_data):
        """Test creating a valid session"""
        response = client.post("/sessions/", json=valid_session_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Test session"
        assert len(data["workouts"]) == 1
    
    def test_unauthorized_session_creation(self, client, valid_session_data):
        """Test that unauthorized requests are rejected"""
        response = client.post("/sessions/", json=valid_session_data)
        # FastAPI with HTTPBearer can return either 401 or 403
        assert response.status_code in [401, 403]
    
    def test_invalid_intensity_rejection(self, client, auth_headers, valid_session_data):
        """Test that invalid intensity is rejected"""
        valid_session_data["workouts"][0]["sets"][0]["reps"]["intensity"] = "EXTREME"
        response = client.post("/sessions/", json=valid_session_data, headers=auth_headers)
        assert response.status_code in [400, 422]
    
    def test_excessive_rep_count_rejection(self, client, auth_headers, valid_session_data):
        """Test that excessive rep count is rejected"""
        valid_session_data["workouts"][0]["sets"][0]["reps"]["count"] = 2000
        response = client.post("/sessions/", json=valid_session_data, headers=auth_headers)
        assert response.status_code in [400, 422]