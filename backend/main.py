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


@app.post("/detect-rooms", response_model=Dict[str, Any])
async def detect_rooms_endpoint(request: RoomDetectionRequest):
    """
    Detect rooms from wall line segments.
    
    Accepts a list of wall segments and returns detected rooms with bounding boxes,
    along with processing metrics (time and confidence score).
    """
    import time
    import json
    import tempfile
    
    start_time = time.time()
    
    try:
        # Convert request to temporary JSON file for processing
        walls_data = [wall.model_dump() for wall in request.walls]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(walls_data, f)
            temp_path = f.name
        
        try:
            # Detect rooms
            rooms = detect_rooms(temp_path, tolerance=1.0)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Calculate overall confidence score (average of all room confidences)
            if rooms:
                overall_confidence = sum(room.get('confidence', 0.5) for room in rooms) / len(rooms)
            else:
                overall_confidence = 0.0
            
            return {
                "rooms": rooms,
                "metrics": {
                    "processing_time": round(processing_time, 3),
                    "confidence_score": round(overall_confidence, 2),
                    "rooms_count": len(rooms)
                }
            }
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


@app.post("/graph-data", response_model=Dict[str, Any])
async def get_graph_data(request: RoomDetectionRequest):
    """
    Get wall adjacency graph data for visualization.
    
    Returns nodes, edges, and detected cycles/faces for graph visualization.
    """
    from src.room_detector import build_wall_graph, find_faces_using_polygonize, find_faces_in_planar_graph, filter_cycles
    from src.parser import parse_line_segments
    from src.graph_serializer import graph_to_json
    import tempfile
    import json
    
    try:
        # Convert request to temporary JSON file for processing
        walls_data = [wall.model_dump() for wall in request.walls]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(walls_data, f)
            temp_path = f.name
        
        try:
            # Parse segments
            segments = parse_line_segments(temp_path)
            
            # Build graph
            graph = build_wall_graph(segments, tolerance=1.0)
            
            # Find faces (same logic as detect_rooms)
            faces = find_faces_using_polygonize(segments)
            if not faces:
                faces = find_faces_in_planar_graph(graph)
            
            # Filter valid faces
            valid_faces = filter_cycles(faces, min_area=100.0, min_perimeter=40.0)
            
            # Serialize graph to JSON
            graph_data = graph_to_json(graph, valid_faces)
            
            return graph_data
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating graph data: {str(e)}")
