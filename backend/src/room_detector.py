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
    uses a combination of cycle_basis and edge-based cycle finding to
    discover all room boundaries, including those formed by internal walls.
    
    Args:
        graph: NetworkX graph of wall connections
        
    Returns:
        List of cycles, where each cycle is a list of node coordinates
    """
    cycles = []
    
    try:
        all_cycles = []
        seen_cycles = set()
        
        # Method 1: Get cycle basis (fundamental cycles)
        try:
            cycle_basis = nx.cycle_basis(graph)
            for cycle in cycle_basis:
                if len(cycle) >= 3:
                    # Normalize: remove duplicate start/end node if present
                    if cycle[0] == cycle[-1]:
                        cycle = cycle[:-1]
                    cycle_tuple = tuple(sorted(cycle))
                    if cycle_tuple not in seen_cycles:
                        seen_cycles.add(cycle_tuple)
                        all_cycles.append(cycle)
        except:
            pass
        
        # Method 2: For each edge, find cycles that include it
        # This helps find cycles that share edges (like internal rooms)
        edges = list(graph.edges())
        for start, end in edges:
            # Create a temporary graph without this edge
            graph_temp = graph.copy()
            graph_temp.remove_edge(start, end)
            
            try:
                # If there's still a path from end to start, we have a cycle
                if nx.has_path(graph_temp, end, start):
                    # Get the shortest alternative path
                    path = nx.shortest_path(graph_temp, end, start)
                    if len(path) >= 2:
                        # Form cycle: start -> end -> path back to start
                        cycle = [start] + path
                        # Remove duplicate if start == end in path
                        if len(cycle) > 1 and cycle[0] == cycle[-1]:
                            cycle = cycle[:-1]
                        
                        if len(cycle) >= 3:
                            cycle_tuple = tuple(sorted(cycle))
                            if cycle_tuple not in seen_cycles:
                                seen_cycles.add(cycle_tuple)
                                all_cycles.append(cycle)
            except:
                pass
        
        # Method 3: Use simple_cycles on directed graph for additional cycles
        # Filter out 2-node cycles (just back-and-forth edges)
        try:
            digraph = graph.to_directed()
            # Limit to reasonable cycle length to avoid explosion
            for cycle in nx.simple_cycles(digraph):
                # Filter out 2-node cycles (not real rooms)
                if 3 <= len(cycle) <= 20:  # Reasonable room size
                    # Remove duplicate start/end node if present
                    if len(cycle) > 1 and cycle[0] == cycle[-1]:
                        cycle = cycle[:-1]
                    # Only add if still valid after removing duplicate
                    if len(cycle) >= 3:
                        cycle_tuple = tuple(sorted(cycle))
                        if cycle_tuple not in seen_cycles:
                            seen_cycles.add(cycle_tuple)
                            all_cycles.append(cycle)
        except:
            pass
        
        cycles = all_cycles
        
    except Exception as e:
        # Final fallback
        try:
            cycle_basis = nx.cycle_basis(graph)
            cycles = [cycle for cycle in cycle_basis if len(cycle) >= 3]
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

