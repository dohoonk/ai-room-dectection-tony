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
    Returns a JSON array of rooms per PRD specification.
    
    Each room contains:
    - id: Unique identifier (e.g., "room_001")
    - bounding_box: Normalized coordinates [x_min, y_min, x_max, y_max] (0-1000 range)
    - name_hint: Optional name hint (e.g., "Room 1")
    """
    import json
    import tempfile
    
    try:
        # Convert request to temporary JSON file for processing
        walls_data = [wall.model_dump() for wall in request.walls]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(walls_data, f)
            temp_path = f.name
        
        try:
            # Detect rooms - returns list of rooms with id, bounding_box, name_hint
            rooms = detect_rooms(temp_path, tolerance=1.0)
            
            # Remove confidence field to match PRD (only id, bounding_box, name_hint)
            # PRD doesn't specify confidence in the output format
            prd_compliant_rooms = []
            for room in rooms:
                prd_compliant_rooms.append({
                    "id": room["id"],
                    "bounding_box": room["bounding_box"],
                    "name_hint": room["name_hint"]
                })
            
            return prd_compliant_rooms
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error detecting rooms: {str(e)}")


@app.get("/test/simple")
async def test_simple():
    """Test endpoint with simple floorplan. Returns PRD-compliant array format."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "tests", "sample_data", "simple", "simple_floorplan.json")
    rooms = detect_rooms(json_path, tolerance=1.0)
    # Return PRD-compliant format (array of rooms)
    prd_compliant_rooms = []
    for room in rooms:
        prd_compliant_rooms.append({
            "id": room["id"],
            "bounding_box": room["bounding_box"],
            "name_hint": room["name_hint"]
        })
    return prd_compliant_rooms


@app.get("/test/complex")
async def test_complex():
    """Test endpoint with complex floorplan. Returns PRD-compliant array format."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "tests", "sample_data", "complex", "complex_floorplan.json")
    rooms = detect_rooms(json_path, tolerance=1.0)
    # Return PRD-compliant format (array of rooms)
    prd_compliant_rooms = []
    for room in rooms:
        prd_compliant_rooms.append({
            "id": room["id"],
            "bounding_box": room["bounding_box"],
            "name_hint": room["name_hint"]
        })
    return prd_compliant_rooms


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
