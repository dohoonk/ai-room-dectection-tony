# Room Detection AI

Automatic detection of room boundaries in architectural floorplans using graph-based algorithms.

## Project Structure

```
.
├── frontend/          # React + Material UI frontend
├── backend/           # Python FastAPI backend
├── tests/             # Test data and utilities
└── .taskmaster/       # Task management files
```

## Development Setup

### Prerequisites
- Node.js v22.20.0+
- Python 3.12.2+
- npm 10.9.3+

### Frontend Setup
```bash
cd frontend
npm install
npm start          # Start development server
npm test           # Run tests
```

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest              # Run tests
```

## Tech Stack

### Frontend
- React (TypeScript)
- Material UI
- Jest + React Testing Library

### Backend
- FastAPI
- NetworkX (graph algorithms)
- Shapely (geometry processing)
- Pytest

## Room Detection Algorithm

### Overview

The room detection algorithm identifies all bounded regions (rooms) in a floorplan by analyzing wall line segments. The system uses a **face-finding algorithm** based on Shapely's `polygonize` function, which is specifically designed to handle multi-room floorplans with internal walls and T-junctions.

### Algorithm Approach

Our implementation uses a **spatial polygonization** approach:

1. **Line Segment Preprocessing**: Wall segments are split at all intersection points to ensure proper region detection
2. **Polygonization**: Shapely's `polygonize` function finds all polygons formed by the line segments
3. **Filtering**: Invalid polygons (too small, invalid geometry) are filtered out
4. **Bounding Box Conversion**: Valid polygons are converted to axis-aligned bounding boxes
5. **Normalization**: Coordinates are normalized to a 0-1000 range

**Key Implementation Details:**
- `split_lines_at_intersections()`: Splits wall segments at intersection points to handle T-junctions
- `find_faces_using_polygonize()`: Primary algorithm using Shapely's polygonize
- `find_faces_in_planar_graph()`: Graph-based fallback using NetworkX for edge cases

### Alternative Approaches Considered

#### 1. Simple Graph Cycle Detection
**Approach**: Use NetworkX's `cycle_basis` or `simple_cycles` to find all cycles in the wall adjacency graph.

**Pros:**
- Simple to implement
- Fast execution
- Works well for simple floorplans

**Cons:**
- ❌ **Cannot detect all rooms in multi-room floorplans** - Only finds a basis of cycles, not all bounded regions
- ❌ **Misses internal rooms** - Rooms formed by T-junctions are not detected
- ❌ **Edge-sharing issues** - Rooms that share edges with the outer perimeter are not properly identified

**Why we didn't choose this**: This approach fails for the MVP requirement of detecting all rooms in multi-room floorplans.

#### 2. Graph-Based Face Finding (Planar Graph Traversal)
**Approach**: Traverse the planar graph using right-hand rule or similar techniques to find all faces.

**Pros:**
- Can theoretically find all faces in a planar graph
- More control over traversal logic
- Can handle complex graph structures

**Cons:**
- ⚠️ **Complex implementation** - Requires careful handling of edge cases
- ⚠️ **Performance concerns** - May be slower for large graphs
- ⚠️ **Reliability issues** - Graph traversal can miss faces in complex topologies
- ⚠️ **T-junction handling** - Requires special logic to handle internal walls

**Why we didn't choose this as primary**: While we implemented this as a fallback, it's more complex and less reliable than polygonization.

#### 3. Spatial Polygonization (Chosen Approach)
**Approach**: Use Shapely's `polygonize` to find all polygons formed by line segments after splitting at intersections.

**Pros:**
- ✅ **Detects all bounded regions** - Finds all rooms, including those with internal walls
- ✅ **Handles T-junctions naturally** - Splitting at intersections ensures proper detection
- ✅ **Robust and reliable** - Shapely is a well-tested geometric library
- ✅ **Simple implementation** - Leverages existing geometric algorithms
- ✅ **Multi-room support** - Successfully detects 3-4 rooms in complex floorplans

**Cons:**
- ⚠️ **Requires line splitting** - Must preprocess segments at intersections
- ⚠️ **Geometry library dependency** - Relies on Shapely's polygonize implementation

**Why we chose this**: This is the only approach that reliably detects all rooms in multi-room floorplans, which is a core MVP requirement.

### Tradeoffs

| Aspect | Simple Cycle Detection | Graph Face Finding | Spatial Polygonization (Our Choice) |
|--------|----------------------|-------------------|-----------------------------------|
| **Multi-room detection** | ❌ Poor | ⚠️ Moderate | ✅ Excellent |
| **T-junction handling** | ❌ Fails | ⚠️ Complex | ✅ Natural |
| **Implementation complexity** | ✅ Simple | ❌ Complex | ✅ Moderate |
| **Performance** | ✅ Fast | ⚠️ Moderate | ✅ Fast |
| **Reliability** | ❌ Low | ⚠️ Moderate | ✅ High |
| **Library dependencies** | ✅ Minimal | ✅ Minimal | ⚠️ Shapely required |

### Algorithm Performance

**Test Results:**
- ✅ Simple floorplans: 1 room detected correctly
- ✅ Multi-room floorplans: 3-4 rooms detected correctly
- ✅ Complex floorplans with internal walls: All bounded regions detected
- ✅ Processing time: < 1 second for typical floorplans

### Fallback Strategy

The algorithm uses a two-tier approach:
1. **Primary**: `find_faces_using_polygonize()` - Uses Shapely's polygonize for robust detection
2. **Fallback**: `find_faces_in_planar_graph()` - Graph-based cycle detection if polygonize fails

This ensures the algorithm works even in edge cases where polygonization might not find regions.

### Future Improvements

Potential enhancements for Phase 2:
- **True polygon output**: Replace bounding boxes with actual room polygons
- **Room classification**: Identify room types (bedroom, kitchen, etc.) using heuristics
- **Confidence scoring**: Calculate detection confidence based on polygon validity and size
- **Performance optimization**: Parallel processing for large floorplans

## Getting Started

See `.taskmaster/tasks/` for detailed task breakdowns.

