# Graph Visualization Manual Testing Guide

## Prerequisites

1. **Backend server running** on `http://localhost:8000`
2. **Frontend server running** on `http://localhost:3000`
3. **Test data files** available in `tests/sample_data/`

## Quick Start

### Step 1: Start Backend Server

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start Frontend Server

In a **new terminal**:

```bash
cd frontend
npm start
```

The browser should automatically open to `http://localhost:3000`

### Step 3: Upload Test File

1. **Click "Upload JSON File"** button
2. **Select a test file** from `tests/sample_data/`:
   - `simple/simple_floorplan.json` - Simple 1-room floorplan
   - `complex/complex_floorplan.json` - Complex 4-room floorplan
   - `test_multiroom_floorplan.json` - 3-room floorplan
   - `irregular_shapes/l_shaped_room.json` - L-shaped room
   - `irregular_shapes/multi_irregular_rooms.json` - Multiple irregular rooms

3. **Wait for processing** - You should see:
   - Loading spinner
   - Metrics display (rooms count, processing time, confidence)
   - Floorplan visualization with detected rooms

### Step 4: Switch to Graph View

1. **Look for the toggle buttons** in the top-right of the visualization panel
2. **Click the "Graph" button** (with tree icon)
   - The button should be enabled if graph data was loaded
   - If disabled, the graph data fetch may have failed

3. **You should now see**:
   - Graph visualization with nodes (blue circles) and edges (gray/red lines)
   - Detected cycles highlighted with colored filled areas
   - Statistics overlay showing node count, edge count, and cycle count

## Testing Graph Visualization Features

### 1. Verify Graph Rendering

**Expected Behavior:**
- ✅ Blue circles represent graph nodes (wall endpoints)
- ✅ Gray lines represent regular walls
- ✅ Red lines represent load-bearing walls (if any)
- ✅ Colored filled areas represent detected cycles/rooms
- ✅ Statistics overlay shows counts

**Test Cases:**
- Simple floorplan: Should show 4 nodes, 4 edges, 1 cycle
- Complex floorplan: Should show multiple nodes, edges, and 4 cycles
- Multi-room floorplan: Should show multiple cycles with different colors

### 2. Test Zoom Controls

**Location**: Top-right corner of graph visualization

**Controls:**
- **Zoom In** (+ icon): Click to zoom in
- **Zoom Out** (- icon): Click to zoom out
- **Fit to Screen** (fit icon): Click to auto-fit graph to viewport

**Expected Behavior:**
- ✅ Zoom in increases graph size
- ✅ Zoom out decreases graph size
- ✅ Fit to screen centers and scales graph appropriately
- ✅ Graph remains visible and centered

**Test Steps:**
1. Click "Zoom In" multiple times - graph should get larger
2. Click "Zoom Out" multiple times - graph should get smaller
3. Click "Fit to Screen" - graph should auto-scale to fit viewport

### 3. Test Pan/Drag

**Method**: Click and drag on the graph canvas

**Expected Behavior:**
- ✅ Mouse cursor changes to "grab" when hovering over graph
- ✅ Cursor changes to "grabbing" when dragging
- ✅ Graph moves smoothly as you drag
- ✅ Graph position persists after releasing mouse

**Test Steps:**
1. Click and hold anywhere on the graph
2. Drag mouse to move graph around
3. Release mouse button
4. Graph should stay in new position

### 4. Test Cycle Highlighting

**Expected Behavior:**
- ✅ Each detected cycle/room has a distinct color
- ✅ Cycles are filled with semi-transparent color
- ✅ Cycle borders are visible with dashed lines
- ✅ Colors are distinct for different cycles

**Test Cases:**
- **Simple floorplan**: 1 cycle (1 room)
- **Complex floorplan**: 4 cycles (4 rooms) with different colors
- **Multi-room floorplan**: 3 cycles with distinct colors

### 5. Test View Toggle

**Location**: Toggle buttons in visualization panel header

**Expected Behavior:**
- ✅ "Rooms" button shows floorplan with room bounding boxes
- ✅ "Graph" button shows graph visualization
- ✅ Toggle switches smoothly between views
- ✅ Graph button is disabled if no graph data available

**Test Steps:**
1. Upload a file and wait for processing
2. Click "Graph" button - should show graph view
3. Click "Rooms" button - should show room visualization
4. Toggle back and forth - both views should work

### 6. Test Statistics Display

**Location**: Top-left corner of graph visualization

**Expected Values:**
- **Nodes**: Number of unique wall endpoints
- **Edges**: Number of wall segments
- **Cycles**: Number of detected rooms/cycles

**Test Cases:**

| Test File | Expected Nodes | Expected Edges | Expected Cycles |
|-----------|---------------|----------------|-----------------|
| `simple_floorplan.json` | 4 | 4 | 1 |
| `complex_floorplan.json` | ~12 | ~8 | 4 |
| `test_multiroom_floorplan.json` | ~10 | ~7 | 3 |

**Verification:**
- ✅ Statistics match expected values
- ✅ Statistics update when new file is uploaded
- ✅ Statistics are visible and readable

## Troubleshooting

### Graph View Button is Disabled

**Possible Causes:**
1. Graph data fetch failed
2. Backend `/graph-data` endpoint not working
3. Network error

**Solutions:**
1. Check browser console for errors
2. Verify backend is running on port 8000
3. Check backend logs for errors
4. Try refreshing the page and uploading again

### Graph Not Rendering

**Possible Causes:**
1. No graph data received
2. SVG rendering issue
3. Invalid graph data format

**Solutions:**
1. Check browser console for errors
2. Verify graph data in Network tab (check `/graph-data` response)
3. Try a different test file
4. Check that nodes and edges arrays are not empty

### Zoom/Pan Not Working

**Possible Causes:**
1. Event handlers not attached
2. SVG element not properly initialized

**Solutions:**
1. Check browser console for errors
2. Verify SVG element is rendered
3. Try clicking directly on the graph area
4. Refresh the page

### Cycles Not Highlighted

**Possible Causes:**
1. No cycles detected
2. Cycle coordinates not matching nodes
3. Rendering issue

**Solutions:**
1. Check statistics - cycle count should be > 0
2. Verify cycles array in graph data
3. Try a different test file with known cycles
4. Check browser console for rendering errors

## Test Checklist

- [ ] Backend server starts successfully
- [ ] Frontend server starts successfully
- [ ] Can upload test JSON file
- [ ] Graph view toggle button appears
- [ ] Can switch to graph view
- [ ] Graph renders with nodes and edges
- [ ] Cycles are highlighted with colors
- [ ] Statistics display shows correct counts
- [ ] Zoom in/out controls work
- [ ] Fit to screen works
- [ ] Pan/drag works smoothly
- [ ] Can toggle back to room view
- [ ] Works with different test files
- [ ] Load-bearing walls show in red (if present)

## Sample Test Files

### Simple Floorplan
**File**: `tests/sample_data/simple/simple_floorplan.json`
- **Expected**: 4 nodes, 4 edges, 1 cycle
- **Use Case**: Basic functionality test

### Complex Floorplan
**File**: `tests/sample_data/complex/complex_floorplan.json`
- **Expected**: ~12 nodes, ~8 edges, 4 cycles
- **Use Case**: Multi-room detection test

### Multi-Room Floorplan
**File**: `tests/sample_data/test_multiroom_floorplan.json`
- **Expected**: ~10 nodes, ~7 edges, 3 cycles
- **Use Case**: Multiple room detection

### Irregular Shapes
**File**: `tests/sample_data/irregular_shapes/multi_irregular_rooms.json`
- **Expected**: Multiple nodes, edges, 3 cycles
- **Use Case**: Irregular shape handling

## API Testing (Optional)

You can also test the `/graph-data` endpoint directly:

```bash
# Test with curl
curl -X POST http://localhost:8000/graph-data \
  -H "Content-Type: application/json" \
  -d @tests/sample_data/simple/simple_floorplan.json
```

**Expected Response:**
```json
{
  "nodes": [...],
  "edges": [...],
  "cycles": [...],
  "stats": {
    "nodeCount": 4,
    "edgeCount": 4,
    "cycleCount": 1
  }
}
```

## Success Criteria

✅ **Graph visualization is functional if:**
- Graph renders correctly with nodes and edges
- Cycles are highlighted with distinct colors
- Zoom and pan controls work smoothly
- Statistics display accurate counts
- View toggle works between rooms and graph
- Works with all test file types

## Next Steps

After manual testing:
1. Verify all features work as expected
2. Test with various floorplan sizes
3. Check performance with large graphs (50+ rooms)
4. Report any issues or improvements needed

