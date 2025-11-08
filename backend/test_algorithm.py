"""Quick test script for room detection algorithm."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.room_detector import detect_rooms
import json

def test_simple_floorplan():
    """Test with simple floorplan."""
    print("Testing Simple Floorplan...")
    print("-" * 50)
    
    json_path = "../tests/sample_data/simple/simple_floorplan.json"
    rooms = detect_rooms(json_path, tolerance=1.0)
    
    print(f"Detected {len(rooms)} room(s):")
    for room in rooms:
        print(f"  {room['id']}: {room['bounding_box']}")
        print(f"    Hint: {room['name_hint']}")
    
    print()
    return rooms

def test_complex_floorplan():
    """Test with complex floorplan."""
    print("Testing Complex Floorplan...")
    print("-" * 50)
    
    json_path = "../tests/sample_data/complex/complex_floorplan.json"
    rooms = detect_rooms(json_path, tolerance=1.0)
    
    print(f"Detected {len(rooms)} room(s):")
    for room in rooms:
        print(f"  {room['id']}: {room['bounding_box']}")
        print(f"    Hint: {room['name_hint']}")
    
    print()
    return rooms

if __name__ == "__main__":
    print("=" * 50)
    print("Room Detection Algorithm Test")
    print("=" * 50)
    print()
    
    try:
        simple_rooms = test_simple_floorplan()
        complex_rooms = test_complex_floorplan()
        
        print("=" * 50)
        print("Summary:")
        print(f"  Simple floorplan: {len(simple_rooms)} rooms detected")
        print(f"  Complex floorplan: {len(complex_rooms)} rooms detected")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

