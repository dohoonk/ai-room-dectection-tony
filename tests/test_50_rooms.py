#!/usr/bin/env python3
"""Test the 50-room floorplan detection."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from src.room_detector import detect_rooms

def main():
    json_path = os.path.join(
        os.path.dirname(__file__),
        'sample_data',
        '50_rooms',
        '50_rooms_floorplan.json'
    )
    
    print(f"Testing 50-room floorplan: {json_path}")
    rooms = detect_rooms(json_path, tolerance=1.0)
    
    print(f'\nDetected {len(rooms)} rooms')
    print(f'Expected: 50 rooms')
    
    if len(rooms) == 50:
        print('✅ SUCCESS: All 50 rooms detected!')
    else:
        print(f'⚠️  Detected {len(rooms)} rooms instead of 50')
    
    # Show first few rooms
    print('\nFirst 5 rooms:')
    for room in rooms[:5]:
        print(f'  {room["id"]}: bbox={room["bounding_box"]}, confidence={room.get("confidence", "N/A")}')
    
    # Show metrics
    if rooms:
        avg_confidence = sum(r.get("confidence", 0) for r in rooms) / len(rooms)
        print(f'\nAverage confidence: {avg_confidence:.2f}')

if __name__ == "__main__":
    main()

