"""Comprehensive unit tests for endpoint snapping and graph construction."""
import pytest
import networkx as nx
from src.parser import WallSegment, parse_line_segments
from src.room_detector import snap_endpoints, build_wall_graph


class TestEndpointSnapping:
    """Test cases for endpoint snapping with various tolerance levels."""
    
    def test_snap_exact_endpoints(self):
        """Test snapping when endpoints are exactly the same."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
        ]
        
        endpoint_map = snap_endpoints(segments, tolerance=1.0)
        
        # All endpoints should map to themselves (exact matches)
        assert endpoint_map[(0.0, 0.0)] == (0.0, 0.0)
        assert endpoint_map[(100.0, 0.0)] == (100.0, 0.0)
        assert endpoint_map[(100.0, 100.0)] == (100.0, 100.0)
    
    def test_snap_within_tolerance(self):
        """Test snapping endpoints that are within tolerance."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.1, 0.1), (100.0, 100.0)),  # Slightly offset
        ]
        
        endpoint_map = snap_endpoints(segments, tolerance=1.0)
        
        # (100.0, 0.0) and (100.1, 0.1) should snap to the same point
        # (distance = sqrt(0.1^2 + 0.1^2) = sqrt(0.02) ≈ 0.14 < 1.0)
        snapped_100_0 = endpoint_map[(100.0, 0.0)]
        snapped_100_1_0_1 = endpoint_map[(100.1, 0.1)]
        
        # They should map to the same canonical point
        assert snapped_100_0 == snapped_100_1_0_1
    
    def test_snap_beyond_tolerance(self):
        """Test that endpoints beyond tolerance are not snapped."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((102.0, 0.0), (100.0, 100.0)),  # Too far (distance = 2.0)
        ]
        
        endpoint_map = snap_endpoints(segments, tolerance=1.0)
        
        # (100.0, 0.0) and (102.0, 0.0) should NOT snap (distance = 2.0 > 1.0)
        assert endpoint_map[(100.0, 0.0)] != endpoint_map[(102.0, 0.0)]
    
    def test_snap_zero_tolerance(self):
        """Test snapping with zero tolerance (only exact matches)."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.1, 0.0), (100.0, 100.0)),  # Very close but not exact
        ]
        
        endpoint_map = snap_endpoints(segments, tolerance=0.0)
        
        # With zero tolerance, even tiny differences should not snap
        assert endpoint_map[(100.0, 0.0)] != endpoint_map[(100.1, 0.0)]
    
    def test_snap_large_tolerance(self):
        """Test snapping with large tolerance."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((105.0, 5.0), (100.0, 100.0)),  # Distance ≈ 7.07
        ]
        
        endpoint_map = snap_endpoints(segments, tolerance=10.0)
        
        # With tolerance 10.0, these should snap
        snapped_100_0 = endpoint_map[(100.0, 0.0)]
        snapped_105_5 = endpoint_map[(105.0, 5.0)]
        assert snapped_100_0 == snapped_105_5
    
    def test_snap_multiple_endpoints(self):
        """Test snapping when multiple endpoints are close together."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.1, 0.1), (100.0, 100.0)),
            WallSegment((99.9, 0.2), (200.0, 0.0)),  # Also close to (100, 0)
        ]
        
        endpoint_map = snap_endpoints(segments, tolerance=1.0)
        
        # All three points near (100, 0) should snap to the same canonical point
        snapped_100_0 = endpoint_map[(100.0, 0.0)]
        snapped_100_1_0_1 = endpoint_map[(100.1, 0.1)]
        snapped_99_9_0_2 = endpoint_map[(99.9, 0.2)]
        
        assert snapped_100_0 == snapped_100_1_0_1 == snapped_99_9_0_2
    
    def test_snap_diagonal_distance(self):
        """Test snapping with diagonal distance calculation."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.7, 0.7), (100.0, 100.0)),  # Diagonal distance ≈ 0.99
        ]
        
        endpoint_map = snap_endpoints(segments, tolerance=1.0)
        
        # Diagonal distance = sqrt(0.7^2 + 0.7^2) ≈ 0.99 < 1.0, should snap
        snapped_100_0 = endpoint_map[(100.0, 0.0)]
        snapped_100_7_0_7 = endpoint_map[(100.7, 0.7)]
        assert snapped_100_0 == snapped_100_7_0_7


class TestGraphConstruction:
    """Test cases for graph construction correctness."""
    
    def test_simple_rectangle_graph(self):
        """Test graph construction for a simple rectangle."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((100.0, 100.0), (0.0, 100.0)),
            WallSegment((0.0, 100.0), (0.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Should have 4 nodes (corners)
        assert len(graph.nodes()) == 4
        # Should have 4 edges (walls)
        assert len(graph.edges()) == 4
        
        # Check that all corners are connected
        assert graph.has_edge((0.0, 0.0), (100.0, 0.0))
        assert graph.has_edge((100.0, 0.0), (100.0, 100.0))
        assert graph.has_edge((100.0, 100.0), (0.0, 100.0))
        assert graph.has_edge((0.0, 100.0), (0.0, 0.0))
    
    def test_graph_with_snapped_endpoints(self):
        """Test graph construction when endpoints are snapped."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.1, 0.1), (100.0, 100.0)),  # Snaps to (100, 0)
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Should have 3 nodes after snapping
        assert len(graph.nodes()) == 3
        # Should have 2 edges
        assert len(graph.edges()) == 2
        
        # The snapped endpoint should create a connection
        # Both segments should connect at the snapped point
        nodes = list(graph.nodes())
        # Find the snapped node (should be one of the canonical points)
        assert (0.0, 0.0) in nodes
        assert (100.0, 100.0) in nodes
    
    def test_graph_preserves_segment_data(self):
        """Test that graph edges preserve segment information."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0), is_load_bearing=True),
            WallSegment((100.0, 0.0), (100.0, 100.0), is_load_bearing=False),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Check that edges have segment data
        for edge in graph.edges(data=True):
            assert 'segment' in edge[2]
            assert isinstance(edge[2]['segment'], WallSegment)
    
    def test_graph_connectivity(self):
        """Test that graph correctly represents wall connectivity."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
            WallSegment((0.0, 0.0), (0.0, 100.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # (0, 0) should be connected to both (100, 0) and (0, 100)
        assert graph.has_edge((0.0, 0.0), (100.0, 0.0))
        assert graph.has_edge((0.0, 0.0), (0.0, 100.0))
        
        # (100, 0) should be connected to (100, 100)
        assert graph.has_edge((100.0, 0.0), (100.0, 100.0))
    
    def test_graph_with_isolated_segment(self):
        """Test graph construction with an isolated segment."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((200.0, 200.0), (300.0, 300.0)),  # Isolated
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Should have 4 nodes
        assert len(graph.nodes()) == 4
        # Should have 2 edges
        assert len(graph.edges()) == 2
        
        # The isolated segment should not connect to the first
        assert not graph.has_edge((100.0, 0.0), (200.0, 200.0))
        assert not graph.has_edge((0.0, 0.0), (200.0, 200.0))


class TestEdgeCases:
    """Test cases for edge cases in graph construction."""
    
    def test_overlapping_endpoints(self):
        """Test handling of overlapping endpoints (same coordinates)."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 0.0)),  # Zero-length segment
            WallSegment((100.0, 0.0), (100.0, 100.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Zero-length segment should still create a self-loop or be handled
        # The graph should have the main connections
        assert (0.0, 0.0) in graph.nodes()
        assert (100.0, 0.0) in graph.nodes()
        assert (100.0, 100.0) in graph.nodes()
    
    def test_single_segment(self):
        """Test graph construction with a single segment."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Should have 2 nodes
        assert len(graph.nodes()) == 2
        # Should have 1 edge
        assert len(graph.edges()) == 1
        assert graph.has_edge((0.0, 0.0), (100.0, 0.0))
    
    def test_empty_segments(self):
        """Test graph construction with empty segment list."""
        segments = []
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Should have no nodes or edges
        assert len(graph.nodes()) == 0
        assert len(graph.edges()) == 0
    
    def test_very_close_but_separate_endpoints(self):
        """Test endpoints that are very close but should remain separate."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.01, 0.0), (200.0, 0.0)),  # Very close but beyond tolerance
        ]
        
        graph = build_wall_graph(segments, tolerance=0.005)  # Very small tolerance
        
        # Should have 4 nodes (not snapped)
        assert len(graph.nodes()) == 4
        # Should have 2 edges
        assert len(graph.edges()) == 2
    
    def test_tolerance_affects_graph_structure(self):
        """Test that different tolerance values produce different graphs."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.5, 0.5), (200.0, 0.0)),
        ]
        
        # Small tolerance - should not snap
        graph_small = build_wall_graph(segments, tolerance=0.1)
        assert len(graph_small.nodes()) == 4
        
        # Large tolerance - should snap
        graph_large = build_wall_graph(segments, tolerance=1.0)
        assert len(graph_large.nodes()) == 3  # One endpoint snapped


class TestGraphStructure:
    """Test cases for overall graph structure verification."""
    
    def test_graph_is_undirected(self):
        """Test that the graph is undirected."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # NetworkX Graph is undirected by default
        assert not graph.is_directed()
    
    def test_graph_node_attributes(self):
        """Test that graph nodes are coordinate tuples."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Nodes should be tuples
        for node in graph.nodes():
            assert isinstance(node, tuple)
            assert len(node) == 2
            assert all(isinstance(coord, float) for coord in node)
    
    def test_graph_edge_attributes(self):
        """Test that graph edges have segment attributes."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0), is_load_bearing=True),
        ]
        
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Check edge attributes
        for u, v, data in graph.edges(data=True):
            assert 'segment' in data
            assert isinstance(data['segment'], WallSegment)
            assert data['segment'].is_load_bearing == True
    
    def test_graph_consistency(self):
        """Test that graph is consistent across multiple calls."""
        segments = [
            WallSegment((0.0, 0.0), (100.0, 0.0)),
            WallSegment((100.0, 0.0), (100.0, 100.0)),
        ]
        
        graph1 = build_wall_graph(segments, tolerance=1.0)
        graph2 = build_wall_graph(segments, tolerance=1.0)
        
        # Should produce identical graphs
        assert set(graph1.nodes()) == set(graph2.nodes())
        assert set(graph1.edges()) == set(graph2.edges())
    
    def test_integration_with_parser(self):
        """Test integration with the parser from Task 3."""
        json_data = [
            {
                "type": "line",
                "start": [0.0, 0.0],
                "end": [100.0, 0.0],
                "is_load_bearing": False
            },
            {
                "type": "line",
                "start": [100.0, 0.0],
                "end": [100.0, 100.0],
                "is_load_bearing": True
            }
        ]
        
        import json
        segments = parse_line_segments(json.dumps(json_data))
        graph = build_wall_graph(segments, tolerance=1.0)
        
        # Should have 3 nodes
        assert len(graph.nodes()) == 3
        # Should have 2 edges
        assert len(graph.edges()) == 2
        
        # Check connectivity
        assert graph.has_edge((0.0, 0.0), (100.0, 0.0))
        assert graph.has_edge((100.0, 0.0), (100.0, 100.0))

