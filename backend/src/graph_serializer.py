"""Serialize NetworkX graph to JSON format for frontend visualization."""
import networkx as nx
from typing import List, Dict, Any, Tuple
from .parser import WallSegment


def graph_to_json(graph: nx.Graph, faces: List[List[Tuple[float, float]]] = None) -> Dict[str, Any]:
    """
    Convert NetworkX graph to JSON format for frontend visualization.
    
    Args:
        graph: NetworkX graph with nodes as coordinates and edges as wall segments
        faces: Optional list of detected faces/cycles to highlight
        
    Returns:
        Dictionary with nodes, edges, and cycles in JSON-serializable format
    """
    # Extract nodes
    nodes = []
    node_index_map = {}  # Map (x, y) -> index
    
    for idx, (x, y) in enumerate(graph.nodes()):
        nodes.append({
            "id": idx,
            "x": float(x),
            "y": float(y),
            "label": f"({x:.1f}, {y:.1f})"
        })
        node_index_map[(x, y)] = idx
    
    # Extract edges
    edges = []
    for edge in graph.edges(data=True):
        start, end, data = edge
        start_idx = node_index_map[start]
        end_idx = node_index_map[end]
        
        # Check if segment exists and has is_load_bearing attribute
        segment = data.get("segment")
        is_load_bearing = False
        if segment and hasattr(segment, "is_load_bearing"):
            is_load_bearing = segment.is_load_bearing
        
        edge_data = {
            "id": f"e_{start_idx}_{end_idx}",
            "source": start_idx,
            "target": end_idx,
            "sourceCoords": [float(start[0]), float(start[1])],
            "targetCoords": [float(end[0]), float(end[1])],
            "isLoadBearing": is_load_bearing
        }
        edges.append(edge_data)
    
    # Convert faces to cycles (using node indices)
    cycles = []
    if faces:
        for cycle_idx, face in enumerate(faces):
            cycle_node_indices = []
            for coord in face:
                # Find closest node index
                coord_tuple = (float(coord[0]), float(coord[1]))
                if coord_tuple in node_index_map:
                    cycle_node_indices.append(node_index_map[coord_tuple])
                else:
                    # If exact match not found, find closest node
                    min_dist = float('inf')
                    closest_idx = None
                    for node_coord, node_idx in node_index_map.items():
                        dist = ((coord[0] - node_coord[0])**2 + (coord[1] - node_coord[1])**2)**0.5
                        if dist < min_dist:
                            min_dist = dist
                            closest_idx = node_idx
                    if closest_idx is not None:
                        cycle_node_indices.append(closest_idx)
            
            if len(cycle_node_indices) >= 3:
                cycles.append({
                    "id": f"cycle_{cycle_idx}",
                    "nodes": cycle_node_indices,
                    "coords": [[float(c[0]), float(c[1])] for c in face]
                })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "cycles": cycles,
        "stats": {
            "nodeCount": len(nodes),
            "edgeCount": len(edges),
            "cycleCount": len(cycles)
        }
    }

