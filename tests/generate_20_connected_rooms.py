#!/usr/bin/env python3
"""
Generate a test floorplan JSON with 20 connected rooms arranged in a grid.
Rooms share walls with adjacent rooms (no gaps between rooms).
"""
import json
import os

def generate_20_connected_rooms_floorplan():
    """
    Generate a floorplan with 20 rooms arranged in a 4x5 grid.
    Rooms share walls with adjacent rooms (connected layout).
    Each room is 180x180 units.
    """
    walls = []
    
    # Grid dimensions: 4 rows x 5 columns = 20 rooms
    rows = 4
    cols = 5
    room_width = 180
    room_height = 180
    
    # Generate outer perimeter walls only
    total_width = cols * room_width
    total_height = rows * room_height
    
    # Top wall (full width)
    walls.append({
        "type": "line",
        "start": [0, 0],
        "end": [total_width, 0],
        "is_load_bearing": False
    })
    
    # Right wall (full height)
    walls.append({
        "type": "line",
        "start": [total_width, 0],
        "end": [total_width, total_height],
        "is_load_bearing": False
    })
    
    # Bottom wall (full width)
    walls.append({
        "type": "line",
        "start": [total_width, total_height],
        "end": [0, total_height],
        "is_load_bearing": False
    })
    
    # Left wall (full height)
    walls.append({
        "type": "line",
        "start": [0, total_height],
        "end": [0, 0],
        "is_load_bearing": False
    })
    
    # Add vertical dividers between columns (internal walls)
    # These must extend the full height to connect with horizontal dividers
    for col in range(1, cols):  # Start from column 1 (skip column 0)
        x = col * room_width
        y_start = 0
        y_end = rows * room_height
        
        walls.append({
            "type": "line",
            "start": [x, y_start],
            "end": [x, y_end],
            "is_load_bearing": False
        })
    
    # Add horizontal dividers between rows (internal walls)
    # These must extend the full width to connect with vertical dividers
    for row in range(1, rows):  # Start from row 1 (skip row 0)
        y = row * room_height
        x_start = 0
        x_end = cols * room_width
        
        walls.append({
            "type": "line",
            "start": [x_start, y],
            "end": [x_end, y],
            "is_load_bearing": False
        })
    
    # Normalize coordinates to 0-1000 range
    # Find min and max coordinates
    all_x = []
    all_y = []
    for wall in walls:
        all_x.extend([wall["start"][0], wall["end"][0]])
        all_y.extend([wall["start"][1], wall["end"][1]])
    
    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)
    
    # Calculate scale factors
    scale_x = 1000 / (max_x - min_x) if (max_x - min_x) > 0 else 1
    scale_y = 1000 / (max_y - min_y) if (max_y - min_y) > 0 else 1
    scale = min(scale_x, scale_y) * 0.95  # Use 95% to add some margin
    
    # Normalize all coordinates
    normalized_walls = []
    for wall in walls:
        normalized_walls.append({
            "type": "line",
            "start": [
                round((wall["start"][0] - min_x) * scale, 2),
                round((wall["start"][1] - min_y) * scale, 2)
            ],
            "end": [
                round((wall["end"][0] - min_x) * scale, 2),
                round((wall["end"][1] - min_y) * scale, 2)
            ],
            "is_load_bearing": False
        })
    
    return normalized_walls

def main():
    """Generate and save the 20-room connected floorplan."""
    walls = generate_20_connected_rooms_floorplan()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), "sample_data", "20_connected_rooms")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save JSON file
    output_path = os.path.join(output_dir, "20_connected_rooms_floorplan.json")
    with open(output_path, 'w') as f:
        json.dump(walls, f, indent=2)
    
    print(f"Generated 20-room connected floorplan with {len(walls)} wall segments")
    print(f"Saved to: {output_path}")
    print(f"\nLayout: 4 rows x 5 columns = 20 rooms")
    print(f"Expected: 20 rooms (all connected, sharing walls)")
    print(f"Wall segments: {len(walls)}")

if __name__ == "__main__":
    main()

