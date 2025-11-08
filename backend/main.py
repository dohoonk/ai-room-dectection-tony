"""FastAPI backend server for Room Detection AI."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))
from src.room_detector import detect_rooms

app = FastAPI(title="Room Detection API", version="0.1.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WallSegment(BaseModel):
    """Wall segment input model."""
    type: str
    start: List[float]
    end: List[float]
    is_load_bearing: bool = False


class RoomDetectionRequest(BaseModel):
    """Request model for room detection."""
    walls: List[WallSegment]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Room Detection API is running!", "status": "ok"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/detect-rooms", response_model=List[Dict[str, Any]])
async def detect_rooms_endpoint(request: RoomDetectionRequest):
    """
    Detect rooms from wall line segments.
    
    Accepts a list of wall segments and returns detected rooms with bounding boxes.
    """
    try:
        # Convert request to temporary JSON file for processing
        import json
        import tempfile
        
        walls_data = [wall.model_dump() for wall in request.walls]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(walls_data, f)
            temp_path = f.name
        
        try:
            # Detect rooms
            rooms = detect_rooms(temp_path, tolerance=1.0)
            return rooms
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error detecting rooms: {str(e)}")


@app.get("/test/simple")
async def test_simple():
    """Test endpoint with simple floorplan."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "tests", "sample_data", "simple", "simple_floorplan.json")
    rooms = detect_rooms(json_path, tolerance=1.0)
    return {
        "rooms": rooms,
        "count": len(rooms),
        "expected": 1
    }


@app.get("/test/complex")
async def test_complex():
    """Test endpoint with complex floorplan."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "tests", "sample_data", "complex", "complex_floorplan.json")
    rooms = detect_rooms(json_path, tolerance=1.0)
    return {
        "rooms": rooms,
        "count": len(rooms),
        "expected": 3,
        "note": "Cycle detection needs improvement for multi-room floorplans"
    }
