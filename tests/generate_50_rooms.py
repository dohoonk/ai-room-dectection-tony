#!/usr/bin/env python3
"""
Generate a test floorplan JSON with 50 rooms arranged in a grid.
"""
import json
import os

def generate_50_room_floorplan():
    """
    Generate a floorplan with 50 rooms arranged in a 5x10 grid.
    Each room is 80x80 units, with 20-unit spacing between rooms.
    """
    walls = []
    
    # Grid dimensions: 5 rows x 10 columns
    rows = 5
    cols = 10
    room_width = 80
    room_height = 80
    spacing = 20  # Space between rooms
    
    # Calculate total dimensions
    total_width = cols * (room_width + spacing) - spacing
    total_height = rows * (room_height + spacing) - spacing
    
    # Generate walls for each room
    for row in range(rows):
        for col in range(cols):
            # Calculate room position
            x_start = col * (room_width + spacing)
            y_start = row * (room_height + spacing)
            x_end = x_start + room_width
            y_end = y_start + room_height
            
            # Room walls (4 walls per room)
            # Top wall
            walls.append({
                "type": "line",
                "start": [x_start, y_start],
                "end": [x_end, y_start],
                "is_load_bearing": False
            })
            
            # Right wall
            walls.append({
                "type": "line",
                "start": [x_end, y_start],
                "end": [x_end, y_end],
                "is_load_bearing": False
            })
            
            # Bottom wall
            walls.append({
                "type": "line",
                "start": [x_end, y_end],
                "end": [x_start, y_end],
                "is_load_bearing": False
            })
            
            # Left wall
            walls.append({
                "type": "line",
                "start": [x_start, y_end],
                "end": [x_start, y_start],
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
    """Generate and save the 50-room floorplan."""
    walls = generate_50_room_floorplan()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), "sample_data", "50_rooms")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save JSON file
    output_path = os.path.join(output_dir, "50_rooms_floorplan.json")
    with open(output_path, 'w') as f:
        json.dump(walls, f, indent=2)
    
    print(f"Generated 50-room floorplan with {len(walls)} wall segments")
    print(f"Saved to: {output_path}")
    print(f"\nExpected: 50 rooms")
    print(f"Wall segments: {len(walls)}")

if __name__ == "__main__":
    main()

