"""Detailed test script showing algorithm results."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.room_detector import detect_rooms, build_wall_graph, detect_cycles, filter_cycles
from src.parser import parse_line_segments
from shapely.geometry import Polygon

def test_with_details(json_path, name):
    """Test algorithm and show detailed results."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    # Parse
    segments = parse_line_segments(json_path)
    print(f"\nParsed {len(segments)} wall segments")
    
    # Build graph
    graph = build_wall_graph(segments, tolerance=1.0)
    print(f"Graph: {len(graph.nodes())} nodes, {len(graph.edges())} edges")
    
    # Detect cycles
    cycles = detect_cycles(graph)
    print(f"Found {len(cycles)} cycles:")
    for i, cycle in enumerate(cycles):
        try:
            poly = Polygon(cycle)
            area = poly.area
            print(f"  Cycle {i+1}: {len(cycle)} nodes, area={area:.1f}")
        except:
            print(f"  Cycle {i+1}: {len(cycle)} nodes (invalid polygon)")
    
    # Filter cycles
    valid_cycles = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
    print(f"After filtering: {len(valid_cycles)} valid cycles")
    
    # Detect rooms
    rooms = detect_rooms(json_path, tolerance=1.0)
    print(f"\nDetected {len(rooms)} room(s):")
    for room in rooms:
        bbox = room['bounding_box']
        print(f"  {room['id']}: bbox={bbox}")
    
    return rooms

if __name__ == "__main__":
    print("Room Detection Algorithm - Detailed Test")
    
    simple_rooms = test_with_details(
        "../tests/sample_data/simple/simple_floorplan.json",
        "Simple Floorplan"
    )
    
    complex_rooms = test_with_details(
        "../tests/sample_data/complex/complex_floorplan.json",
        "Complex Floorplan"
    )
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Simple: {len(simple_rooms)} rooms (expected: 1) ✓" if len(simple_rooms) == 1 else f"  Simple: {len(simple_rooms)} rooms (expected: 1)")
    print(f"  Complex: {len(complex_rooms)} rooms (expected: 3)" + (" ✓" if len(complex_rooms) == 3 else " ⚠ (needs improvement)"))
    print(f"{'='*60}")
    print("\nNote: Complex floorplan cycle detection needs improvement")
    print("      to find all room faces, not just fundamental cycles.")

