# Sample Test Data

This directory contains sample blueprint data for testing the room detection algorithm.

## Structure

```
sample_data/
├── simple/
│   ├── simple_floorplan.json    # Simple single-room floorplan
│   └── simple_floorplan.png     # Visual representation
├── complex/
│   ├── complex_floorplan.json    # Multi-room floorplan with corridors
│   └── complex_floorplan.png     # Visual representation
└── README.md                     # This file
```

## Data Format

### JSON Format
Each JSON file contains an array of wall line segments:
```json
[
  {
    "type": "line",
    "start": [x, y],
    "end": [x, y],
    "is_load_bearing": boolean
  }
]
```

- Coordinates are normalized to 0-1000 range
- `start` and `end` are [x, y] coordinate pairs
- `is_load_bearing` indicates structural walls (thicker lines in images)

### Image Format
- PNG format, 1000x1000 pixels
- White background with light gray grid (100px spacing)
- Black/dark gray lines for walls
- Red dots at wall endpoints
- Load-bearing walls are thicker and darker

## Test Cases

### Simple Floorplan
- **Expected Rooms**: 1 room
- **Description**: Single rectangular room (100,100) to (400,300)
- **Use Case**: Basic room detection validation

### Complex Floorplan
- **Expected Rooms**: 3 rooms
- **Description**: 
  - Room 1: Left side (50,50) to (250,200)
  - Room 2: Top right (250,50) to (450,200)
  - Room 3: Bottom right (250,200) to (450,350)
- **Use Case**: Multi-room detection, corridor handling

## Verification Steps

1. **JSON Validation**:
   - Verify JSON syntax is valid
   - Check all required fields are present
   - Ensure coordinates are within 0-1000 range

2. **Image Validation**:
   - Open PNG file and verify walls are visible
   - Check that wall lines match JSON coordinates
   - Verify load-bearing walls are thicker

3. **Data Consistency**:
   - Compare JSON coordinates with image visualization
   - Ensure all wall endpoints connect properly
   - Verify closed loops can be formed

## Regenerating Images

To regenerate images from JSON files:
```bash
cd tests
python3 generate_blueprint_images.py
```

