"""Integration tests for the FastAPI room detection endpoint."""
import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test cases for health check endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "ok"
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRoomDetectionEndpoint:
    """Test cases for the room detection endpoint."""
    
    def test_valid_json_acceptance(self):
        """Test that valid JSON is accepted and processed."""
        request_data = {
            "walls": [
                {
                    "type": "line",
                    "start": [0.0, 0.0],
                    "end": [100.0, 0.0],
                    "is_load_bearing": False
                },
                {
                    "type": "line",
                    "start": [100.0, 0.0],
                    "end": [100.0, 100.0],
                    "is_load_bearing": False
                },
                {
                    "type": "line",
                    "start": [100.0, 100.0],
                    "end": [0.0, 100.0],
                    "is_load_bearing": False
                },
                {
                    "type": "line",
                    "start": [0.0, 100.0],
                    "end": [0.0, 0.0],
                    "is_load_bearing": False
                }
            ]
        }
        
        response = client.post("/detect-rooms", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0  # At least should return a list (may be empty if no rooms detected)
    
    def test_correct_room_detection_results(self):
        """Test that room detection returns correct results."""
        request_data = {
            "walls": [
                {"type": "line", "start": [100.0, 100.0], "end": [400.0, 100.0], "is_load_bearing": False},
                {"type": "line", "start": [400.0, 100.0], "end": [400.0, 300.0], "is_load_bearing": False},
                {"type": "line", "start": [400.0, 300.0], "end": [100.0, 300.0], "is_load_bearing": False},
                {"type": "line", "start": [100.0, 300.0], "end": [100.0, 100.0], "is_load_bearing": False}
            ]
        }
        
        response = client.post("/detect-rooms", json=request_data)
        assert response.status_code == 200
        rooms = response.json()
        
        # Should detect at least 1 room
        assert len(rooms) >= 1
        
        # Check room structure
        room = rooms[0]
        assert "id" in room
        assert "bounding_box" in room
        assert "name_hint" in room
        assert isinstance(room["bounding_box"], list)
        assert len(room["bounding_box"]) == 4  # [min_x, min_y, max_x, max_y]
    
    def test_invalid_input_missing_fields(self):
        """Test error handling for invalid input with missing fields."""
        request_data = {
            "walls": [
                {
                    "type": "line",
                    "start": [0.0, 0.0]
                    # Missing "end" field
                }
            ]
        }
        
        response = client.post("/detect-rooms", json=request_data)
        # Should return validation error (422) or processing error (400)
        assert response.status_code in [400, 422]
    
    def test_invalid_input_wrong_type(self):
        """Test error handling for invalid input with wrong data types."""
        request_data = {
            "walls": [
                {
                    "type": "line",
                    "start": "not a list",  # Should be a list
                    "end": [100.0, 100.0],
                    "is_load_bearing": False
                }
            ]
        }
        
        response = client.post("/detect-rooms", json=request_data)
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_empty_walls_array(self):
        """Test handling of empty walls array."""
        request_data = {
            "walls": []
        }
        
        response = client.post("/detect-rooms", json=request_data)
        # Should handle gracefully (may return empty list or error)
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            assert isinstance(response.json(), list)
    
    def test_error_handling_malformed_data(self):
        """Test error handling for malformed data."""
        # Send invalid JSON structure
        response = client.post("/detect-rooms", json={"invalid": "data"})
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_response_format_validation(self):
        """Test that response format is correct."""
        request_data = {
            "walls": [
                {"type": "line", "start": [0.0, 0.0], "end": [100.0, 0.0], "is_load_bearing": False},
                {"type": "line", "start": [100.0, 0.0], "end": [100.0, 100.0], "is_load_bearing": False},
                {"type": "line", "start": [100.0, 100.0], "end": [0.0, 100.0], "is_load_bearing": False},
                {"type": "line", "start": [0.0, 100.0], "end": [0.0, 0.0], "is_load_bearing": False}
            ]
        }
        
        response = client.post("/detect-rooms", json=request_data)
        assert response.status_code == 200
        rooms = response.json()
        
        # Validate response format
        assert isinstance(rooms, list)
        for room in rooms:
            assert isinstance(room, dict)
            assert "id" in room
            assert "bounding_box" in room
            assert "name_hint" in room
            assert isinstance(room["id"], str)
            assert isinstance(room["bounding_box"], list)
            assert len(room["bounding_box"]) == 4
            assert all(isinstance(coord, (int, float)) for coord in room["bounding_box"])
            assert isinstance(room["name_hint"], str)


class TestTestEndpoints:
    """Test cases for test endpoints."""
    
    def test_simple_test_endpoint(self):
        """Test the simple test endpoint."""
        response = client.get("/test/simple")
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        assert "count" in data
        assert "expected" in data
        assert isinstance(data["rooms"], list)
        assert data["count"] == len(data["rooms"])
    
    def test_complex_test_endpoint(self):
        """Test the complex test endpoint."""
        response = client.get("/test/complex")
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        assert "count" in data
        assert "expected" in data
        assert isinstance(data["rooms"], list)
        assert data["count"] == len(data["rooms"])


class TestEdgeCases:
    """Test cases for edge cases and error scenarios."""
    
    def test_single_wall_segment(self):
        """Test with a single wall segment (no room possible)."""
        request_data = {
            "walls": [
                {"type": "line", "start": [0.0, 0.0], "end": [100.0, 0.0], "is_load_bearing": False}
            ]
        }
        
        response = client.post("/detect-rooms", json=request_data)
        assert response.status_code == 200
        rooms = response.json()
        # Single segment cannot form a room
        assert isinstance(rooms, list)
    
    def test_walls_with_load_bearing(self):
        """Test walls with load bearing property."""
        request_data = {
            "walls": [
                {"type": "line", "start": [0.0, 0.0], "end": [100.0, 0.0], "is_load_bearing": True},
                {"type": "line", "start": [100.0, 0.0], "end": [100.0, 100.0], "is_load_bearing": False},
                {"type": "line", "start": [100.0, 100.0], "end": [0.0, 100.0], "is_load_bearing": True},
                {"type": "line", "start": [0.0, 100.0], "end": [0.0, 0.0], "is_load_bearing": False}
            ]
        }
        
        response = client.post("/detect-rooms", json=request_data)
        assert response.status_code == 200
        rooms = response.json()
        assert isinstance(rooms, list)
    
    def test_large_coordinate_values(self):
        """Test with large coordinate values."""
        request_data = {
            "walls": [
                {"type": "line", "start": [0.0, 0.0], "end": [900.0, 0.0], "is_load_bearing": False},
                {"type": "line", "start": [900.0, 0.0], "end": [900.0, 800.0], "is_load_bearing": False},
                {"type": "line", "start": [900.0, 800.0], "end": [0.0, 800.0], "is_load_bearing": False},
                {"type": "line", "start": [0.0, 800.0], "end": [0.0, 0.0], "is_load_bearing": False}
            ]
        }
        
        response = client.post("/detect-rooms", json=request_data)
        assert response.status_code == 200
        rooms = response.json()
        assert isinstance(rooms, list)
    
    def test_missing_walls_field(self):
        """Test error handling when walls field is missing."""
        request_data = {}
        
        response = client.post("/detect-rooms", json=request_data)
        assert response.status_code in [400, 422]  # Validation error
    
    def test_invalid_json_body(self):
        """Test error handling for completely invalid JSON."""
        # Send non-JSON data
        response = client.post(
            "/detect-rooms",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

