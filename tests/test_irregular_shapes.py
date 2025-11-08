#!/usr/bin/env python3
"""
Test room detection with irregular/non-rectangular shapes.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from src.room_detector import detect_rooms

def test_irregular_shapes():
    """Test all irregular shape floorplans."""
    base_dir = Path(__file__).parent / "sample_data" / "irregular_shapes"
    
    test_files = [
        ("l_shaped_room.json", 1, "L-shaped room"),
        ("t_shaped_room.json", 1, "T-shaped room"),
        ("irregular_pentagon.json", 1, "Irregular pentagon room"),
        ("hexagon_room.json", 1, "Regular hexagon room"),
        ("trapezoid_room.json", 1, "Trapezoid room"),
        ("multi_irregular_rooms.json", 3, "Multiple irregular-shaped rooms"),
        ("angled_walls_room.json", 1, "Room with angled walls"),
    ]
    
    print("=" * 80)
    print("TESTING IRREGULAR SHAPE DETECTION")
    print("=" * 80)
    print()
    
    results = []
    for filename, expected_rooms, description in test_files:
        filepath = base_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  {description}: File not found - {filepath}")
            continue
        
        try:
            rooms = detect_rooms(str(filepath), tolerance=1.0)
            detected_count = len(rooms)
            
            status = "✅" if detected_count == expected_rooms else "❌"
            match_status = "PASS" if detected_count == expected_rooms else f"FAIL (expected {expected_rooms}, got {detected_count})"
            
            print(f"{status} {description}")
            print(f"   File: {filename}")
            print(f"   Expected: {expected_rooms} room(s)")
            print(f"   Detected: {detected_count} room(s)")
            print(f"   Status: {match_status}")
            
            if rooms:
                avg_confidence = sum(r.get('confidence', 0) for r in rooms) / len(rooms)
                print(f"   Avg Confidence: {avg_confidence:.2f}")
                print(f"   Room IDs: {[r['id'] for r in rooms]}")
            
            results.append({
                'file': filename,
                'description': description,
                'expected': expected_rooms,
                'detected': detected_count,
                'passed': detected_count == expected_rooms,
                'rooms': rooms
            })
            print()
            
        except Exception as e:
            print(f"❌ {description}: ERROR - {str(e)}")
            print(f"   File: {filepath}")
            print()
            results.append({
                'file': filename,
                'description': description,
                'expected': expected_rooms,
                'detected': 0,
                'passed': False,
                'error': str(e)
            })
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total = len(results)
    passed = sum(1 for r in results if r.get('passed', False))
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {passed/total*100:.1f}%")
    print()
    
    if failed > 0:
        print("Failed Tests:")
        for r in results:
            if not r.get('passed', False):
                print(f"  - {r['description']}: Expected {r['expected']}, got {r['detected']}")
                if 'error' in r:
                    print(f"    Error: {r['error']}")
    
    return results

if __name__ == "__main__":
    test_irregular_shapes()

