#!/usr/bin/env python3
"""Test the 20-room connected floorplan detection."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from src.room_detector import detect_rooms

def main():
    json_path = os.path.join(
        os.path.dirname(__file__),
        'sample_data',
        '20_connected_rooms',
        '20_connected_rooms_floorplan.json'
    )
    
    print(f"Testing 20-room connected floorplan: {json_path}")
    rooms = detect_rooms(json_path, tolerance=1.0)
    
    print(f'\nDetected {len(rooms)} rooms')
    print(f'Expected: 20 rooms')
    
    if len(rooms) == 20:
        print('✅ SUCCESS: All 20 rooms detected!')
    else:
        print(f'⚠️  Detected {len(rooms)} rooms instead of 20')
    
    # Show first few rooms
    print('\nFirst 5 rooms:')
    for room in rooms[:5]:
        print(f'  {room["id"]}: bbox={room["bounding_box"]}, confidence={room.get("confidence", "N/A")}')
    
    # Show metrics
    if rooms:
        avg_confidence = sum(r.get("confidence", 0) for r in rooms) / len(rooms)
        print(f'\nAverage confidence: {avg_confidence:.2f}')
        print(f'Confidence range: {min(r.get("confidence", 0) for r in rooms):.2f} - {max(r.get("confidence", 0) for r in rooms):.2f}')

if __name__ == "__main__":
    main()

