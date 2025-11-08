"""Core room detection algorithm using graph-based cycle detection."""
import networkx as nx
from shapely.geometry import Polygon, box
from typing import List, Dict, Tuple
from .parser import WallSegment


def snap_endpoints(segments: List[WallSegment], tolerance: float = 1.0) -> Dict[Tuple[float, float], Tuple[float, float]]:
    """
    Snap endpoints within tolerance to form connected groups.
    
    Args:
        segments: List of wall segments
        tolerance: Maximum distance for endpoints to be considered the same
        
    Returns:
        Dictionary mapping original endpoints to snapped (canonical) endpoints
    """
    all_endpoints = set()
    for segment in segments:
        all_endpoints.add(segment.start)
        all_endpoints.add(segment.end)
    
    # Group endpoints by proximity
    endpoint_groups = {}
    canonical_points = []
    
    for point in all_endpoints:
        # Find if this point is close to any canonical point
        assigned = False
        for canonical in canonical_points:
            distance = ((point[0] - canonical[0])**2 + (point[1] - canonical[1])**2)**0.5
            if distance <= tolerance:
                endpoint_groups[point] = canonical
                assigned = True
                break
        
        if not assigned:
            # This is a new canonical point
            canonical_points.append(point)
            endpoint_groups[point] = point
    
    return endpoint_groups


def build_wall_graph(segments: List[WallSegment], tolerance: float = 1.0) -> nx.Graph:
    """
    Build a graph from wall segments by snapping endpoints.
    
    Args:
        segments: List of wall segments
        tolerance: Maximum distance for endpoints to be considered the same
        
    Returns:
        NetworkX graph where nodes are snapped endpoints and edges are wall segments
    """
    endpoint_map = snap_endpoints(segments, tolerance)
    
    G = nx.Graph()
    
    for segment in segments:
        start_snapped = endpoint_map[segment.start]
        end_snapped = endpoint_map[segment.end]
        
        # Add nodes if they don't exist
        G.add_node(start_snapped)
        G.add_node(end_snapped)
        
        # Add edge representing the wall segment
        G.add_edge(start_snapped, end_snapped, segment=segment)
    
    return G


def detect_cycles(graph: nx.Graph) -> List[List[Tuple[float, float]]]:
    """
    Detect all cycles (closed loops) in the graph.
    
    For floorplans, we need to find all faces/regions. This implementation
    uses cycle_basis and also finds cycles by exploring alternative paths.
    
    Args:
        graph: NetworkX graph of wall connections
        
    Returns:
        List of cycles, where each cycle is a list of node coordinates
    """
    cycles = []
    
    try:
        # Get fundamental cycles
        cycle_basis = nx.cycle_basis(graph)
        all_cycles = []
        
        # Add cycles from basis
        for cycle in cycle_basis:
            if len(cycle) >= 3:
                all_cycles.append(cycle)
        
        # Find additional cycles by exploring paths between nodes
        # For each pair of connected nodes, try to find alternative paths
        nodes = list(graph.nodes())
        for i, start in enumerate(nodes):
            for end in graph.neighbors(start):
                # Try to find alternative path from end to start
                graph_temp = graph.copy()
                graph_temp.remove_edge(start, end)
                
                try:
                    if nx.has_path(graph_temp, end, start):
                        path = nx.shortest_path(graph_temp, end, start)
                        if len(path) >= 3:
                            # Form cycle: start -> end -> path back to start
                            cycle = [start] + [end] + path[1:]
                            # Check if this is a new cycle
                            cycle_set = set(cycle)
                            is_new = True
                            for existing in all_cycles:
                                if set(existing) == cycle_set:
                                    is_new = False
                                    break
                            if is_new and len(cycle) >= 3:
                                all_cycles.append(cycle)
                except:
                    pass
        
        # Remove duplicates
        unique_cycles = []
        seen = set()
        for cycle in all_cycles:
            cycle_tuple = tuple(sorted(cycle))
            if cycle_tuple not in seen:
                seen.add(cycle_tuple)
                unique_cycles.append(cycle)
        
        cycles = unique_cycles
        
    except Exception as e:
        # Fallback
        try:
            cycles = nx.cycle_basis(graph)
        except:
            cycles = []
    
    return cycles


def _find_cycle_from_edge(graph: nx.Graph, start: Tuple, end: Tuple, visited: set) -> List:
    """Helper to find a cycle starting from a specific edge."""
    # Simple DFS to find cycle
    stack = [(end, [start, end])]
    visited_edges = visited.copy()
    visited_edges.add(tuple(sorted([start, end])))
    
    while stack:
        current, path = stack.pop()
        
        if current == start and len(path) > 2:
            return path
        
        for neighbor in graph.neighbors(current):
            edge = tuple(sorted([current, neighbor]))
            if edge not in visited_edges and neighbor != path[-2] if len(path) > 1 else True:
                visited_edges.add(edge)
                stack.append((neighbor, path + [neighbor]))
    
    return None


def filter_cycles(cycles: List[List[Tuple[float, float]]], 
                 min_area: float = 100.0,
                 min_perimeter: float = 40.0,
                 max_area: float = 900000.0) -> List[List[Tuple[float, float]]]:
    """
    Filter cycles to keep only valid room-sized polygons.
    
    Args:
        cycles: List of cycles (lists of coordinates)
        min_area: Minimum area for a valid room
        min_perimeter: Minimum perimeter for a valid room
        max_area: Maximum area to filter out outer perimeter
        
    Returns:
        Filtered list of cycles
    """
    valid_cycles = []
    
    for cycle in cycles:
        if len(cycle) < 3:
            continue
        
        try:
            # Create polygon from cycle
            polygon = Polygon(cycle)
            
            # Check if polygon is valid
            if not polygon.is_valid:
                continue
            
            area = polygon.area
            perimeter = polygon.length
            
            # Filter by size (exclude too large cycles which are likely outer perimeter)
            if (area >= min_area and area <= max_area and 
                perimeter >= min_perimeter):
                valid_cycles.append(cycle)
        except:
            # Skip invalid polygons
            continue
    
    return valid_cycles


def polygon_to_bounding_box(cycle: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """
    Convert a polygon cycle to an axis-aligned bounding box.
    
    Args:
        cycle: List of coordinates forming a closed polygon
        
    Returns:
        Tuple (min_x, min_y, max_x, max_y)
    """
    if len(cycle) == 0:
        return (0, 0, 0, 0)
    
    x_coords = [p[0] for p in cycle]
    y_coords = [p[1] for p in cycle]
    
    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def normalize_bounding_box(bbox: Tuple[float, float, float, float], 
                          target_range: Tuple[int, int] = (0, 1000)) -> Tuple[float, float, float, float]:
    """
    Normalize bounding box coordinates to target range while preserving aspect ratio.
    
    Args:
        bbox: Bounding box (min_x, min_y, max_x, max_y)
        target_range: Target coordinate range (min, max)
        
    Returns:
        Normalized bounding box
    """
    min_x, min_y, max_x, max_y = bbox
    min_val, max_val = target_range
    
    # If already in range, return as-is
    if (min_x >= min_val and max_x <= max_val and 
        min_y >= min_val and max_y <= max_val):
        return bbox
    
    # Calculate current dimensions
    width = max_x - min_x
    height = max_y - min_y
    
    if width == 0 or height == 0:
        return bbox
    
    # Calculate scale factor to fit in target range
    scale_x = (max_val - min_val) / width if width > 0 else 1.0
    scale_y = (max_val - min_val) / height if height > 0 else 1.0
    scale = min(scale_x, scale_y)  # Preserve aspect ratio
    
    # Apply scaling
    new_width = width * scale
    new_height = height * scale
    
    # Center in target range
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    new_min_x = max(min_val, center_x - new_width / 2)
    new_min_y = max(min_val, center_y - new_height / 2)
    new_max_x = min(max_val, new_min_x + new_width)
    new_max_y = min(max_val, new_min_y + new_height)
    
    return (new_min_x, new_min_y, new_max_x, new_max_y)


def detect_rooms(json_path: str, tolerance: float = 1.0) -> List[Dict]:
    """
    Main function to detect rooms from wall line segments.
    
    Args:
        json_path: Path to JSON file with wall segments
        tolerance: Tolerance for endpoint snapping
        
    Returns:
        List of detected rooms with bounding boxes
    """
    from .parser import parse_line_segments
    
    # Parse line segments
    segments = parse_line_segments(json_path)
    
    # Build wall graph
    graph = build_wall_graph(segments, tolerance)
    
    # Detect cycles
    cycles = detect_cycles(graph)
    
    # Filter cycles
    valid_cycles = filter_cycles(cycles, min_area=100.0, min_perimeter=40.0)
    
    # Convert to bounding boxes
    rooms = []
    for i, cycle in enumerate(valid_cycles):
        bbox = polygon_to_bounding_box(cycle)
        normalized_bbox = normalize_bounding_box(bbox)
        
        rooms.append({
            "id": f"room_{i+1:03d}",
            "bounding_box": list(normalized_bbox),
            "name_hint": f"Room {i+1}"
        })
    
    return rooms

