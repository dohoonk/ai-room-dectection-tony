# Test Cases for Sample Data

This document outlines test cases for verifying the accuracy and correctness of sample test data.

## Test Case 1: Simple Floorplan JSON Structure

**Objective**: Verify the simple floorplan JSON has correct structure and format.

**Steps**:
1. Load `simple/simple_floorplan.json`
2. Verify it's valid JSON
3. Check it's an array
4. Verify each wall segment has:
   - `type` field equals "line"
   - `start` is a 2-element array of numbers
   - `end` is a 2-element array of numbers
   - `is_load_bearing` is a boolean
5. Verify coordinates are within 0-1000 range

**Expected Result**: All validations pass, JSON structure is correct.

**Expected Rooms**: 1 room (rectangular: 100,100 to 400,300)

---

## Test Case 2: Complex Floorplan JSON Structure

**Objective**: Verify the complex floorplan JSON has correct structure and format.

**Steps**:
1. Load `complex/complex_floorplan.json`
2. Verify it's valid JSON
3. Check it's an array with 8 wall segments
4. Verify each wall segment has required fields
5. Verify coordinates are within 0-1000 range
6. Check that walls form closed loops

**Expected Result**: All validations pass, JSON structure is correct.

**Expected Rooms**: 3 rooms
- Room 1: Left (50,50 to 250,200)
- Room 2: Top right (250,50 to 450,200)
- Room 3: Bottom right (250,200 to 450,350)

---

## Test Case 3: Image-JSON Correspondence (Simple)

**Objective**: Verify the simple floorplan image matches the JSON data.

**Steps**:
1. Open `simple/simple_floorplan.png`
2. Verify image is 1000x1000 pixels
3. Check that wall lines are visible
4. Compare wall positions in image with JSON coordinates:
   - Top wall: y=100, x from 100 to 400
   - Right wall: x=400, y from 100 to 300
   - Bottom wall: y=300, x from 100 to 400
   - Left wall: x=100, y from 100 to 300
5. Verify red endpoint markers match JSON start/end points

**Expected Result**: Image accurately represents JSON wall data.

---

## Test Case 4: Image-JSON Correspondence (Complex)

**Objective**: Verify the complex floorplan image matches the JSON data.

**Steps**:
1. Open `complex/complex_floorplan.png`
2. Verify image is 1000x1000 pixels
3. Check that all 8 wall segments are visible
4. Verify load-bearing walls (outer walls) are thicker
5. Compare wall positions with JSON coordinates
6. Verify three distinct room areas are visible

**Expected Result**: Image accurately represents JSON wall data with correct room divisions.

---

## Test Case 5: Coordinate Normalization

**Objective**: Verify all coordinates are properly normalized to 0-1000 range.

**Steps**:
1. Load both JSON files
2. Extract all start and end coordinates
3. Verify all x coordinates are between 0 and 1000
4. Verify all y coordinates are between 0 and 1000
5. Check for any negative values or values > 1000

**Expected Result**: All coordinates are within valid range.

---

## Test Case 6: Wall Connectivity

**Objective**: Verify walls connect properly to form closed loops.

**Steps**:
1. Load JSON files
2. Extract all endpoints (start and end points)
3. Group endpoints that should connect (within small tolerance)
4. Verify that walls form closed polygons
5. Check for isolated wall segments

**Expected Result**: 
- Simple: 4 walls form 1 closed rectangle
- Complex: 8 walls form 3 closed rectangles

---

## Test Case 7: Load-Bearing Wall Identification

**Objective**: Verify load-bearing walls are correctly marked.

**Steps**:
1. Load complex floorplan JSON
2. Identify walls with `is_load_bearing: true`
3. Verify these are the outer perimeter walls
4. Check that internal walls have `is_load_bearing: false`
5. Verify in image that load-bearing walls are thicker

**Expected Result**: 
- Complex floorplan: 4 outer walls are load-bearing
- Internal walls are not load-bearing

---

## Manual Verification Checklist

- [ ] Simple floorplan JSON is valid and well-formed
- [ ] Complex floorplan JSON is valid and well-formed
- [ ] Simple floorplan image displays correctly
- [ ] Complex floorplan image displays correctly
- [ ] Image coordinates match JSON coordinates
- [ ] All walls are visible in images
- [ ] Load-bearing walls are visually distinct
- [ ] Expected number of rooms can be identified visually
- [ ] No coordinate values outside 0-1000 range
- [ ] Documentation is clear and complete

---

## Expected Detection Results

When the room detection algorithm processes these files:

### Simple Floorplan
- **Detected Rooms**: 1
- **Bounding Box**: [100, 100, 400, 300]
- **Confidence**: High (simple, closed rectangle)

### Complex Floorplan
- **Detected Rooms**: 3
- **Room 1 Bounding Box**: [50, 50, 250, 200]
- **Room 2 Bounding Box**: [250, 50, 450, 200]
- **Room 3 Bounding Box**: [250, 200, 450, 350]
- **Confidence**: High (clear room boundaries)

