import pytest
from datetime import datetime, timedelta
from src.validation.validation import (
    sanitize_string,
    validate_workout_name,
    validate_intensity,
    validate_rep_count,
    validate_weight
)

class TestSanitizeString:
    def test_normal_string(self):
        result = sanitize_string("Normal workout name")
        assert result == "Normal workout name"
    
    def test_html_escape(self):
        result = sanitize_string("<script>alert('xss')</script>")
        # Should escape HTML characters - the exact format may vary
        assert "<script>" not in result
        assert "script" in result  # The word should still be there, just escaped
        # Check that some form of escaping occurred (escaped version is longer)
        assert len(result) > len("<script>alert('xss')</script>")
    
    def test_sql_injection_attempt(self):
        result = sanitize_string("'; DROP TABLE users; --")
        # Should block SQL injection patterns
        assert "[BLOCKED]" in result.lower() or "drop table" not in result.lower()
        assert ";" not in result
        assert "--" not in result
    
    def test_semicolon_removal(self):
        result = sanitize_string("test; malicious")
        assert ";" not in result
    
    def test_comment_removal(self):
        result = sanitize_string("test -- comment")
        assert "--" not in result

class TestValidateWorkoutName:
    def test_valid_names(self):
        valid_names = ["Bench Press", "Pull-ups", "Squat_123", "Deadlift (Heavy)"]
        for name in valid_names:
            result = validate_workout_name(name)
            assert result == name
    
    def test_empty_name(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_workout_name("")
    
    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_workout_name("Bench@Press")

class TestValidateIntensity:
    def test_valid_intensities(self):
        for intensity in ["low", "medium", "high"]:
            result = validate_intensity(intensity)
            assert result == intensity
    
    def test_invalid_intensity(self):
        with pytest.raises(ValueError, match="Invalid intensity"):
            validate_intensity("extreme")

class TestValidateRepCount:
    def test_valid_counts(self):
        for count in [1, 5, 10, 50, 100]:
            result = validate_rep_count(count)
            assert result == count
    
    def test_invalid_counts(self):
        with pytest.raises(ValueError):
            validate_rep_count(0)
        with pytest.raises(ValueError):
            validate_rep_count(1001)

class TestValidateWeight:
    def test_valid_weights(self):
        for weight in [None, 0, 45, 135, 225]:
            result = validate_weight(weight)
            assert result == weight
    
    def test_invalid_weights(self):
        with pytest.raises(ValueError):
            validate_weight(-10)
        with pytest.raises(ValueError):
            validate_weight(10001)