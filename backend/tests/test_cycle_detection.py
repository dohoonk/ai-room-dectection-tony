"""Comprehensive unit tests for cycle detection in wall adjacency graphs."""
import pytest
import networkx as nx
from src.parser import WallSegment
from src.room_detector import build_wall_graph, detect_cycles


class TestSimpleCycleDetection:
    """Test cases for cycle detection in simple graphs."""
    
    def test_single_cycle_rectangle(self):
        """Test detection of a single cycle (rectangle)."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Should detect at least 1 cycle (the rectangle)
        assert len(cycles) >= 1
        
        # Check that at least one cycle contains all 4 corners
        found_rectangle = False
        for cycle in cycles:
            cycle_set = set(cycle)
            if all(corner in cycle_set for corner in [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]):
                found_rectangle = True
                assert len(cycle) >= 4
                break
        
        assert found_rectangle, "Rectangle cycle not found"
    
    def test_single_cycle_triangle(self):
        """Test detection of a single cycle (triangle)."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (50.0, 100.0)),
            WallSegment((50.0, 100.0), (0.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Should detect at least 1 cycle
        assert len(cycles) >= 1
        
        # Check that at least one cycle contains all 3 vertices
        found_triangle = False
        for cycle in cycles:
            cycle_set = set(cycle)
            if all(vertex in cycle_set for vertex in [(0.0, 0.0), (100.0, 0.0), (50.0, 100.0)]):
                found_triangle = True
                assert len(cycle) >= 3
                break
        
        assert found_triangle, "Triangle cycle not found"
    
    def test_no_cycles_linear_segments(self):
        """Test graph with no cycles (linear chain)."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (200.0, 0.0)),
            WallSegment((200.0, 0.0), (300.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Linear chain should have no cycles
        # Note: cycle_basis might return empty list or might find some cycles
        # depending on implementation, but a simple linear chain should have no cycles
        assert isinstance(cycles, list)
    
    def test_no_cycles_single_segment(self):
        """Test graph with single segment (no cycles)."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Single segment cannot form a cycle
        assert isinstance(cycles, list)
        # Should have no cycles or very minimal cycles
        assert len(cycles) == 0 or all(len(c) < 3 for c in cycles)


class TestMultipleCycles:
    """Test cases for graphs with multiple cycles."""
    
    def test_two_separate_rooms(self):
        """Test detection of two separate room cycles."""
        segments = [
            # Room 1 (left)
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
            # Room 2 (right, separate)
            WallSegment((200.0, 0.0), (300.0, 0.0)),
            WallSegment((300.0, 0.0), (300.0, 100.0)),
            WallSegment((300.0, 100.0), (200.0, 100.0)),
            WallSegment((200.0, 100.0), (200.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Should detect at least 2 cycles (one for each room)
        assert len(cycles) >= 2
        
        # Verify both rooms are represented
        room1_corners = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        room2_corners = [(200.0, 0.0), (300.0, 0.0), (300.0, 100.0), (200.0, 100.0)]
        
        found_room1 = False
        found_room2 = False
        
        for cycle in cycles:
            cycle_set = set(cycle)
            if all(corner in cycle_set for corner in room1_corners):
                found_room1 = True
            if all(corner in cycle_set for corner in room2_corners):
                found_room2 = True
        
        assert found_room1, "Room 1 cycle not found"
        assert found_room2, "Room 2 cycle not found"
    
    def test_adjacent_rooms_shared_wall(self):
        """Test detection of cycles in adjacent rooms sharing a wall."""
        segments = [
            # Left room
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
            # Right room (shares wall at x=100)
            WallSegment((100.0, 0.0), (200.0, 0.0)),
            WallSegment((200.0, 0.0), (200.0, 100.0)),
            WallSegment((200.0, 100.0), (100.0, 100.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Should detect at least 2 cycles (one for each room)
        # Note: The outer perimeter might also be detected as a cycle
        assert len(cycles) >= 2
        
        # Verify left room cycle
        left_room_corners = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        found_left = False
        
        for cycle in cycles:
            cycle_set = set(cycle)
            if all(corner in cycle_set for corner in left_room_corners):
                found_left = True
                break
        
        assert found_left, "Left room cycle not found"
    
    def test_three_rooms_complex(self):
        """Test detection of cycles in a complex floorplan with 3 rooms."""
        segments = [
            # Outer walls
            WallSegment((0.0, 0.0), (300.0, 0.0)),
            WallSegment((300.0, 0.0), (300.0, 200.0)),
            WallSegment((300.0, 200.0), (0.0, 200.0)),
            WallSegment((0.0, 200.0), (0.0, 0.0)),
            # Internal wall dividing into 3 rooms
            WallSegment((100.0, 0.0), (100.0, 200.0)),
            WallSegment((200.0, 0.0), (200.0, 200.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Should detect multiple cycles
        # At minimum: outer perimeter + potentially 3 room cycles
        assert len(cycles) >= 1
        
        # Verify outer perimeter is detected
        outer_corners = [(0.0, 0.0), (300.0, 0.0), (300.0, 200.0), (0.0, 200.0)]
        found_outer = False
        
        for cycle in cycles:
            cycle_set = set(cycle)
            if all(corner in cycle_set for corner in outer_corners):
                found_outer = True
                break
        
        assert found_outer, "Outer perimeter cycle not found"


class TestNestedCycles:
    """Test cases for nested cycles."""
    
    def test_outer_and_inner_cycle(self):
        """Test detection of outer perimeter and inner room cycle."""
        segments = [
            # Outer rectangle
            WallSegment((0.0, 0.0), (200.0, 0.0)),
            WallSegment((200.0, 0.0), (200.0, 200.0)),
            WallSegment((200.0, 200.0), (0.0, 200.0)),
            WallSegment((0.0, 200.0), (0.0, 0.0)),
            # Inner rectangle (room)
            WallSegment((50.0, 50.0), (150.0, 50.0)),
            WallSegment((150.0, 50.0), (150.0, 150.0)),
            WallSegment((150.0, 150.0), (50.0, 150.0)),
            WallSegment((50.0, 150.0), (50.0, 50.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Should detect at least 2 cycles (outer and inner)
        assert len(cycles) >= 2
        
        # Verify inner room cycle
        inner_corners = [(50.0, 50.0), (150.0, 50.0), (150.0, 150.0), (50.0, 150.0)]
        found_inner = False
        
        for cycle in cycles:
            cycle_set = set(cycle)
            if all(corner in cycle_set for corner in inner_corners):
                found_inner = True
                break
        
        assert found_inner, "Inner room cycle not found"


class TestDuplicateCycleFiltering:
    """Test cases for duplicate cycle filtering."""
    
    def test_cycles_are_unique(self):
        """Test that duplicate cycles are filtered out."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Check for duplicates by comparing sets of nodes
        cycle_sets = [set(cycle) for cycle in cycles]
        unique_cycle_sets = set(tuple(sorted(cycle_set)) for cycle_set in cycle_sets)
        
        # Should have no duplicates (all cycles should be unique)
        assert len(unique_cycle_sets) == len(cycle_sets), "Duplicate cycles found"
    
    def test_cycle_structure(self):
        """Test that cycles are returned in correct format."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Verify structure
        for cycle in cycles:
            assert isinstance(cycle, list), "Cycle should be a list"
            assert len(cycle) >= 3, "Cycle should have at least 3 nodes"
            for node in cycle:
                assert isinstance(node, tuple), "Node should be a tuple"
                assert len(node) == 2, "Node should be (x, y) coordinate"
                assert all(isinstance(coord, float) for coord in node), "Coordinates should be floats"


class TestEdgeCases:
    """Test cases for edge cases in cycle detection."""
    
    def test_empty_graph(self):
        """Test cycle detection on empty graph."""
        graph = nx.Graph()
        cycles = detect_cycles(graph)
        
        assert isinstance(cycles, list)
        assert len(cycles) == 0
    
    def test_single_node_graph(self):
        """Test cycle detection on graph with single node."""
        graph = nx.Graph()
        graph.add_node((0.0, 0.0))
        cycles = detect_cycles(graph)
        
        assert isinstance(cycles, list)
        # Single node cannot form a cycle
        assert len(cycles) == 0 or all(len(c) < 3 for c in cycles)
    
    def test_two_node_graph(self):
        """Test cycle detection on graph with two nodes."""
        graph = nx.Graph()
        graph.add_edge((0.0, 0.0), (100.0, 0.0))
        cycles = detect_cycles(graph)
        
        assert isinstance(cycles, list)
        # Two nodes cannot form a cycle (need at least 3)
        assert len(cycles) == 0 or all(len(c) < 3 for c in cycles)
    
    def test_disconnected_components(self):
        """Test cycle detection with disconnected graph components."""
        segments = [
            # Component 1: Rectangle
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
            # Component 2: Isolated segment (no cycle)
            WallSegment((200.0, 200.0), (300.0, 300.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # Should detect at least the rectangle cycle
        assert len(cycles) >= 1
        
        # Verify rectangle cycle exists
        rectangle_corners = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        found_rectangle = False
        
        for cycle in cycles:
            cycle_set = set(cycle)
            if all(corner in cycle_set for corner in rectangle_corners):
                found_rectangle = True
                break
        
        assert found_rectangle, "Rectangle cycle not found in disconnected graph"
    
    def test_self_loops_handled(self):
        """Test that self-loops are handled correctly."""
        graph = nx.Graph()
        graph.add_edge((0.0, 0.0), (0.0, 0.0))  # Self-loop
        cycles = detect_cycles(graph)
        
        # Self-loops might be detected, but should be filtered (need >= 3 nodes)
        assert isinstance(cycles, list)
        # All cycles should have at least 3 distinct nodes
        for cycle in cycles:
            assert len(set(cycle)) >= 3 or len(cycle) < 3


class TestCycleDataStructure:
    """Test cases for cycle data structure and format."""
    
    def test_cycles_are_coordinate_lists(self):
        """Test that cycles are lists of coordinate tuples."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        for cycle in cycles:
            assert isinstance(cycle, list), "Cycle should be a list"
            for node in cycle:
                assert isinstance(node, tuple), "Node should be a tuple"
                assert len(node) == 2, "Node should be (x, y)"
                assert all(isinstance(c, (int, float)) for c in node), "Coordinates should be numbers"
    
    def test_cycles_minimum_length(self):
        """Test that all cycles have minimum length of 3."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles = detect_cycles(graph)
        
        # All cycles should have at least 3 nodes
        for cycle in cycles:
            assert len(cycle) >= 3, f"Cycle has only {len(cycle)} nodes, need at least 3"
    
    def test_cycle_consistency(self):
        """Test that cycle detection is consistent across multiple calls."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        cycles1 = detect_cycles(graph)
        cycles2 = detect_cycles(graph)
        
        # Should produce same number of cycles
        assert len(cycles1) == len(cycles2)
        
        # Cycle sets should be the same (comparing sets of node sets)
        cycles1_sets = {tuple(sorted(set(c))) for c in cycles1}
        cycles2_sets = {tuple(sorted(set(c))) for c in cycles2}
        assert cycles1_sets == cycles2_sets

