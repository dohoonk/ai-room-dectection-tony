#!/usr/bin/env python3
"""
Generate test floorplans with irregular/non-rectangular room shapes.

Creates various test cases:
- L-shaped rooms
- T-shaped rooms
- Irregular polygon rooms
- Rooms with multiple vertices
- Rooms with angled walls
"""
import json
import os
from pathlib import Path

def create_l_shaped_room():
    """Create an L-shaped room."""
    walls = [
        # Outer walls forming L-shape
        {"type": "line", "start": [0, 0], "end": [300, 0], "is_load_bearing": True},
        {"type": "line", "start": [300, 0], "end": [300, 200], "is_load_bearing": True},
        {"type": "line", "start": [300, 200], "end": [200, 200], "is_load_bearing": True},
        {"type": "line", "start": [200, 200], "end": [200, 400], "is_load_bearing": True},
        {"type": "line", "start": [200, 400], "end": [0, 400], "is_load_bearing": True},
        {"type": "line", "start": [0, 400], "end": [0, 0], "is_load_bearing": True},
    ]
    return walls

def create_t_shaped_room():
    """Create a T-shaped room."""
    walls = [
        # Outer walls forming T-shape
        {"type": "line", "start": [0, 0], "end": [400, 0], "is_load_bearing": True},
        {"type": "line", "start": [400, 0], "end": [400, 200], "is_load_bearing": True},
        {"type": "line", "start": [400, 200], "end": [500, 200], "is_load_bearing": True},
        {"type": "line", "start": [500, 200], "end": [500, 400], "is_load_bearing": True},
        {"type": "line", "start": [500, 400], "end": [200, 400], "is_load_bearing": True},
        {"type": "line", "start": [200, 400], "end": [200, 200], "is_load_bearing": True},
        {"type": "line", "start": [200, 200], "end": [0, 200], "is_load_bearing": True},
        {"type": "line", "start": [0, 200], "end": [0, 0], "is_load_bearing": True},
    ]
    return walls

def create_irregular_pentagon_room():
    """Create an irregular pentagon-shaped room."""
    walls = [
        {"type": "line", "start": [100, 0], "end": [300, 0], "is_load_bearing": True},
        {"type": "line", "start": [300, 0], "end": [400, 150], "is_load_bearing": True},
        {"type": "line", "start": [400, 150], "end": [350, 350], "is_load_bearing": True},
        {"type": "line", "start": [350, 350], "end": [150, 400], "is_load_bearing": True},
        {"type": "line", "start": [150, 400], "end": [0, 250], "is_load_bearing": True},
        {"type": "line", "start": [0, 250], "end": [50, 100], "is_load_bearing": True},
        {"type": "line", "start": [50, 100], "end": [100, 0], "is_load_bearing": True},
    ]
    return walls

def create_hexagon_room():
    """Create a regular hexagon-shaped room."""
    import math
    center_x, center_y = 250, 250
    radius = 200
    walls = []
    
    # Create hexagon with 6 sides
    points = []
    for i in range(6):
        angle = math.radians(60 * i)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append((x, y))
    
    # Close the polygon
    points.append(points[0])
    
    for i in range(len(points) - 1):
        walls.append({
            "type": "line",
            "start": list(points[i]),
            "end": list(points[i + 1]),
            "is_load_bearing": True
        })
    
    return walls

def create_trapezoid_room():
    """Create a trapezoid-shaped room."""
    walls = [
        {"type": "line", "start": [50, 0], "end": [350, 0], "is_load_bearing": True},
        {"type": "line", "start": [350, 0], "end": [400, 300], "is_load_bearing": True},
        {"type": "line", "start": [400, 300], "end": [0, 300], "is_load_bearing": True},
        {"type": "line", "start": [0, 300], "end": [50, 0], "is_load_bearing": True},
    ]
    return walls

def create_multi_room_with_irregular_shapes():
    """Create a floorplan with multiple rooms of different shapes."""
    walls = [
        # Room 1: L-shaped
        {"type": "line", "start": [0, 0], "end": [200, 0], "is_load_bearing": True},
        {"type": "line", "start": [200, 0], "end": [200, 150], "is_load_bearing": True},
        {"type": "line", "start": [200, 150], "end": [100, 150], "is_load_bearing": True},
        {"type": "line", "start": [100, 150], "end": [100, 300], "is_load_bearing": True},
        {"type": "line", "start": [100, 300], "end": [0, 300], "is_load_bearing": True},
        {"type": "line", "start": [0, 300], "end": [0, 0], "is_load_bearing": True},
        
        # Room 2: Trapezoid
        {"type": "line", "start": [250, 0], "end": [450, 0], "is_load_bearing": True},
        {"type": "line", "start": [450, 0], "end": [500, 200], "is_load_bearing": True},
        {"type": "line", "start": [500, 200], "end": [300, 200], "is_load_bearing": True},
        {"type": "line", "start": [300, 200], "end": [250, 0], "is_load_bearing": True},
        
        # Room 3: Irregular pentagon
        {"type": "line", "start": [250, 250], "end": [400, 250], "is_load_bearing": True},
        {"type": "line", "start": [400, 250], "end": [450, 350], "is_load_bearing": True},
        {"type": "line", "start": [450, 350], "end": [350, 450], "is_load_bearing": True},
        {"type": "line", "start": [350, 450], "end": [200, 400], "is_load_bearing": True},
        {"type": "line", "start": [200, 400], "end": [200, 300], "is_load_bearing": True},
        {"type": "line", "start": [200, 300], "end": [250, 250], "is_load_bearing": True},
    ]
    return walls

def create_angled_walls_room():
    """Create a room with angled walls (not axis-aligned)."""
    walls = [
        {"type": "line", "start": [0, 0], "end": [200, 100], "is_load_bearing": True},
        {"type": "line", "start": [200, 100], "end": [300, 0], "is_load_bearing": True},
        {"type": "line", "start": [300, 0], "end": [400, 200], "is_load_bearing": True},
        {"type": "line", "start": [400, 200], "end": [300, 400], "is_load_bearing": True},
        {"type": "line", "start": [300, 400], "end": [100, 350], "is_load_bearing": True},
        {"type": "line", "start": [100, 350], "end": [0, 200], "is_load_bearing": True},
        {"type": "line", "start": [0, 200], "end": [0, 0], "is_load_bearing": True},
    ]
    return walls

def main():
    """Generate all irregular shape test files."""
    base_dir = Path(__file__).parent / "sample_data" / "irregular_shapes"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    test_cases = [
        ("l_shaped_room", create_l_shaped_room, "L-shaped room"),
        ("t_shaped_room", create_t_shaped_room, "T-shaped room"),
        ("irregular_pentagon", create_irregular_pentagon_room, "Irregular pentagon room"),
        ("hexagon_room", create_hexagon_room, "Regular hexagon room"),
        ("trapezoid_room", create_trapezoid_room, "Trapezoid room"),
        ("multi_irregular_rooms", create_multi_room_with_irregular_shapes, "Multiple irregular-shaped rooms"),
        ("angled_walls_room", create_angled_walls_room, "Room with angled walls"),
    ]
    
    for filename, create_func, description in test_cases:
        walls = create_func()
        filepath = base_dir / f"{filename}.json"
        
        with open(filepath, 'w') as f:
            json.dump(walls, f, indent=2)
        
        print(f"Created {description}: {filepath}")
        print(f"  Walls: {len(walls)}")
    
    print(f"\nGenerated {len(test_cases)} irregular shape test files in {base_dir}")

if __name__ == "__main__":
    main()

