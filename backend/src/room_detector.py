"""Core room detection algorithm using graph-based cycle detection."""
import networkx as nx
from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union, polygonize
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


def traverse_face(graph: nx.Graph, start_node: Tuple, start_edge: Tuple, visited_edges: set) -> List[Tuple[float, float]]:
    """
    Traverse a face starting from a specific edge using right-hand rule.
    
    Args:
        graph: NetworkX graph
        start_node: Starting node
        start_edge: (start_node, next_node) edge to start from
        visited_edges: Set of visited edges to avoid revisiting
        
    Returns:
        List of nodes forming the face, or None if face is invalid
    """
    face = [start_node]
    current_node = start_edge[1]
    prev_node = start_node
    edge_key = tuple(sorted([start_node, current_node]))
    
    if edge_key in visited_edges:
        return None
    
    visited_edges.add(edge_key)
    
    # Traverse the face
    max_iterations = len(graph.nodes()) * 2
    iterations = 0
    
    while current_node != start_node and iterations < max_iterations:
        iterations += 1
        face.append(current_node)
        
        # Get neighbors of current node
        neighbors = list(graph.neighbors(current_node))
        
        if len(neighbors) == 0:
            return None
        
        # Find next node using right-hand rule (turn right at each junction)
        # Calculate angles to find the rightmost turn
        next_node = None
        best_angle = float('-inf')
        
        for neighbor in neighbors:
            if neighbor == prev_node:
                continue
            
            # Calculate angle from prev->current to current->neighbor
            dx1 = current_node[0] - prev_node[0]
            dy1 = current_node[1] - prev_node[1]
            dx2 = neighbor[0] - current_node[0]
            dy2 = neighbor[1] - current_node[1]
            
            # Cross product to determine turn direction (right = positive)
            cross = dx1 * dy2 - dy1 * dx2
            # Dot product for angle magnitude
            dot = dx1 * dx2 + dy1 * dy2
            angle = cross  # Positive = right turn
            
            if angle > best_angle:
                best_angle = angle
                next_node = neighbor
        
        if next_node is None:
            # No valid next node
            return None
        
        edge_key = tuple(sorted([current_node, next_node]))
        if edge_key in visited_edges and next_node != start_node:
            # Already visited this edge (but might be completing the cycle)
            if next_node == start_node and len(face) >= 3:
                return face
            return None
        
        visited_edges.add(edge_key)
        prev_node = current_node
        current_node = next_node
    
    if current_node == start_node and len(face) >= 3:
        return face
    
    return None


def split_lines_at_intersections(lines: List[LineString]) -> List[LineString]:
    """
    Split line strings at all intersection points.
    
    This ensures that polygonize can find all bounded regions,
    including those formed by internal walls that create T-junctions.
    
    Args:
        lines: List of LineString objects
        
    Returns:
        List of split LineString objects
    """
    if not lines:
        return []
    
    # Collect all intersection points
    intersection_points = set()
    for i, line1 in enumerate(lines):
        for line2 in lines[i+1:]:
            if line1.intersects(line2):
                intersection = line1.intersection(line2)
                if isinstance(intersection, Point):
                    intersection_points.add((intersection.x, intersection.y))
                elif hasattr(intersection, 'geoms'):
                    # Multiple intersection points
                    for geom in intersection.geoms:
                        if isinstance(geom, Point):
                            intersection_points.add((geom.x, geom.y))
    
    if not intersection_points:
        return lines
    
    # Split each line at intersection points
    split_lines = []
    for line in lines:
        # Get all intersection points on this line
        line_intersections = []
        for point in intersection_points:
            pt = Point(point)
            if line.distance(pt) < 0.1:  # Point is on or very close to line
                line_intersections.append(point)
        
        if not line_intersections:
            # No intersections on this line
            split_lines.append(line)
            continue
        
        # Sort intersection points along the line
        start = (line.coords[0][0], line.coords[0][1])
        end = (line.coords[-1][0], line.coords[-1][1])
        
        # Calculate distances from start to each intersection
        def dist_from_start(pt):
            return ((pt[0] - start[0])**2 + (pt[1] - start[1])**2)**0.5
        
        line_intersections.sort(key=dist_from_start)
        
        # Create segments between intersection points
        current_start = start
        for intersection in line_intersections:
            if current_start != intersection:
                segment = LineString([current_start, intersection])
                if segment.length > 0.1:  # Ignore very short segments
                    split_lines.append(segment)
            current_start = intersection
        
        # Add final segment
        if current_start != end:
            segment = LineString([current_start, end])
            if segment.length > 0.1:
                split_lines.append(segment)
    
    return split_lines


def find_faces_using_polygonize(segments: List[WallSegment]) -> List[List[Tuple[float, float]]]:
    """
    Find all bounded regions using Shapely's polygonize.
    
    This treats wall segments as line strings, splits them at intersections,
    and finds all polygons formed by them, which represents all rooms.
    For multi-room floorplans, this finds all regions including those
    formed by internal walls.
    
    Args:
        segments: List of wall segments
        
    Returns:
        List of faces, where each face is a list of node coordinates forming a cycle
    """
    faces = []
    
    try:
        # Create LineString objects from wall segments
        lines = []
        for segment in segments:
            line = LineString([segment.start, segment.end])
            lines.append(line)
        
        # Split lines at intersection points
        # This is crucial for finding internal rooms
        split_lines = split_lines_at_intersections(lines)
        
        # Use polygonize to find all polygons formed by the split lines
        # This should now find all bounded regions including internal rooms
        polygons = list(polygonize(split_lines))
        
        # Convert polygons to cycles (lists of coordinates)
        for poly in polygons:
            if poly.is_valid and poly.area > 0:
                # Get exterior coordinates
                coords = list(poly.exterior.coords)
                # Remove duplicate last point (polygon closes itself)
                if len(coords) > 1 and coords[0] == coords[-1]:
                    coords = coords[:-1]
                if len(coords) >= 3:
                    faces.append([(float(x), float(y)) for x, y in coords])
    
    except Exception as e:
        pass
    
    return faces


def find_faces_in_planar_graph(graph: nx.Graph) -> List[List[Tuple[float, float]]]:
    """
    Find all faces (bounded regions) in a planar graph.
    
    This uses multiple strategies to find all room boundaries:
    1. Find all simple cycles in the directed graph
    2. Use edge removal to find alternative paths (cycles that share edges)
    3. Filter to find minimal faces (rooms)
    
    Args:
        graph: NetworkX graph of wall connections
        
    Returns:
        List of faces, where each face is a list of node coordinates forming a cycle
    """
    faces = []
    
    if len(graph.nodes()) < 3:
        return faces
    
    try:
        all_cycles = []
        seen_cycles = set()
        
        # Strategy 1: Find all simple cycles in directed graph
        digraph = graph.to_directed()
        for cycle in nx.simple_cycles(digraph):
            if len(cycle) < 3:
                continue
            # Remove duplicate start/end
            if len(cycle) > 1 and cycle[0] == cycle[-1]:
                cycle = cycle[:-1]
            if len(cycle) < 3:
                continue
            
            # Canonical representation for deduplication
            cycle_tuple = tuple(sorted(cycle))
            if cycle_tuple not in seen_cycles:
                seen_cycles.add(cycle_tuple)
                all_cycles.append(cycle)
        
        # Strategy 2: For each edge, find cycles that include it
        # This finds cycles that share edges (like internal rooms)
        edges = list(graph.edges())
        for start, end in edges:
            graph_temp = graph.copy()
            graph_temp.remove_edge(start, end)
            
            try:
                if nx.has_path(graph_temp, end, start):
                    # Find all simple paths (not just shortest)
                    try:
                        for path in nx.all_simple_paths(graph_temp, end, start, cutoff=15):
                            if len(path) >= 2:
                                cycle = [start] + path
                                if len(cycle) > 1 and cycle[0] == cycle[-1]:
                                    cycle = cycle[:-1]
                                if len(cycle) >= 3:
                                    cycle_tuple = tuple(sorted(cycle))
                                    if cycle_tuple not in seen_cycles:
                                        seen_cycles.add(cycle_tuple)
                                        all_cycles.append(cycle)
                    except:
                        # Fallback to shortest path if all_simple_paths is too slow
                        path = nx.shortest_path(graph_temp, end, start)
                        if len(path) >= 2:
                            cycle = [start] + path
                            if len(cycle) > 1 and cycle[0] == cycle[-1]:
                                cycle = cycle[:-1]
                            if len(cycle) >= 3:
                                cycle_tuple = tuple(sorted(cycle))
                                if cycle_tuple not in seen_cycles:
                                    seen_cycles.add(cycle_tuple)
                                    all_cycles.append(cycle)
            except:
                pass
        
        # Strategy 3: Filter to find minimal faces (rooms)
        # A minimal face is one that doesn't contain other smaller faces
        valid_faces = []
        cycle_polygons = {}
        
        # Convert all cycles to polygons
        for cycle in all_cycles:
            try:
                poly = Polygon(cycle)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                if poly.is_valid:
                    cycle_polygons[tuple(cycle)] = poly
            except:
                continue
        
        # Find minimal faces
        for cycle, poly in cycle_polygons.items():
            is_minimal = True
            cycle_area = poly.area
            
            # Check if this cycle contains other smaller cycles
            for other_cycle, other_poly in cycle_polygons.items():
                if cycle == other_cycle:
                    continue
                
                try:
                    # If other cycle is significantly smaller and inside this one
                    if (other_poly.area < cycle_area * 0.8 and 
                        poly.contains(other_poly)):
                        is_minimal = False
                        break
                except:
                    continue
            
            if is_minimal:
                valid_faces.append(list(cycle))
        
        faces = valid_faces
        
    except Exception as e:
        # Fallback to cycle basis
        try:
            cycle_basis = nx.cycle_basis(graph)
            faces = [cycle for cycle in cycle_basis if len(cycle) >= 3]
        except:
            faces = []
    
    return faces


def detect_cycles(graph: nx.Graph) -> List[List[Tuple[float, float]]]:
    """
    Detect all cycles (closed loops) in the graph using face-finding algorithm.
    
    For floorplans, we need to find all faces/regions. This implementation
    uses a face-finding algorithm that identifies all bounded regions in the
    planar graph, including internal rooms formed by walls that share edges.
    
    Args:
        graph: NetworkX graph of wall connections
        
    Returns:
        List of cycles, where each cycle is a list of node coordinates
    """
    # Use face-finding algorithm for better multi-room detection
    cycles = find_faces_in_planar_graph(graph)
    
    # If face-finding didn't find cycles, fall back to basic cycle detection
    if not cycles:
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


def calculate_confidence_score(face: List[Tuple[float, float]], 
                              total_faces: int,
                              used_polygonize: bool) -> float:
    """
    Calculate confidence score (0.00-1.00) for a detected room.
    
    Factors considered:
    - Polygon validity and regularity
    - Room size (not too small, not too large)
    - Detection method (polygonize is more reliable)
    - Number of vertices (more vertices = more complex, potentially less reliable)
    
    Args:
        face: List of coordinates forming the room boundary
        total_faces: Total number of faces detected
        used_polygonize: Whether polygonize was used (more reliable)
        
    Returns:
        Confidence score between 0.00 and 1.00
    """
    try:
        polygon = Polygon(face)
        
        # Base score from polygon validity
        if not polygon.is_valid:
            return 0.3  # Low confidence for invalid polygons
        
        score = 0.5  # Base score for valid polygon
        
        # Boost for using polygonize (more reliable method)
        if used_polygonize:
            score += 0.2
        
        # Check polygon regularity (compactness)
        area = polygon.area
        perimeter = polygon.length
        
        if area > 0 and perimeter > 0:
            # Compactness ratio (4π*area/perimeter²) - closer to 1.0 is more circular/regular
            compactness = (4 * 3.14159 * area) / (perimeter * perimeter)
            # Regular shapes score higher
            if compactness > 0.5:
                score += 0.15
            elif compactness > 0.3:
                score += 0.1
            elif compactness > 0.1:
                score += 0.05
        
        # Size-based confidence (rooms that are too small or too large are less reliable)
        if 500 <= area <= 500000:  # Reasonable room size range
            score += 0.1
        elif area < 500:
            score -= 0.1  # Very small rooms might be noise
        elif area > 500000:
            score -= 0.05  # Very large might be outer perimeter
        
        # Vertex count (too many vertices might indicate complex/irregular shape)
        vertex_count = len(face)
        if 3 <= vertex_count <= 8:
            score += 0.05  # Simple shapes are more reliable
        elif vertex_count > 20:
            score -= 0.05  # Very complex shapes might be less reliable
        
        # Normalize to 0.00-1.00 range
        return max(0.0, min(1.0, score))
        
    except Exception:
        return 0.2  # Low confidence if we can't evaluate


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
    
    # Try polygonize first (finds all regions formed by line segments)
    faces = find_faces_using_polygonize(segments)
    used_polygonize = len(faces) > 0
    
    # If polygonize didn't find faces, fall back to graph-based approach
    if not faces:
        # Build wall graph
        graph = build_wall_graph(segments, tolerance)
        
        # Detect cycles using face-finding
        faces = find_faces_in_planar_graph(graph)
    
    # Filter faces to get valid rooms
    valid_faces = filter_cycles(faces, min_area=100.0, min_perimeter=40.0)
    
    # Convert to bounding boxes
    rooms = []
    for i, face in enumerate(valid_faces):
        bbox = polygon_to_bounding_box(face)
        normalized_bbox = normalize_bounding_box(bbox)
        
        # Calculate confidence score for this room
        confidence = calculate_confidence_score(face, len(valid_faces), used_polygonize)
        
        rooms.append({
            "id": f"room_{i+1:03d}",
            "bounding_box": list(normalized_bbox),
            "name_hint": f"Room {i+1}",
            "confidence": round(confidence, 2)
        })
    
    return rooms

