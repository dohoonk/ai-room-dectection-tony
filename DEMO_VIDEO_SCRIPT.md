# Room Detection AI - Demo Video Script

## Overview
This document provides a script and outline for creating a demo video showcasing the Room Detection AI application. The video should demonstrate the complete workflow from uploading a floorplan to interacting with detected rooms.

## Video Duration
Target: 2-3 minutes

## Demo Script

### Introduction (0:00 - 0:15)
**Visual**: Show the application interface
**Narration**: 
> "Welcome to Room Detection AI. This tool automatically detects room boundaries in architectural floorplans, reducing manual tracing time from 5-15 minutes to under 3 seconds."

**Key Points**:
- Show the clean, modern Material UI interface
- Highlight the "Upload JSON File" button

---

### Step 1: Upload Floorplan (0:15 - 0:30)
**Visual**: 
- Click "Upload JSON File" button
- Select a floorplan JSON file (use `20_connected_rooms_floorplan.json` or `50_rooms_floorplan.json`)
- Show loading state

**Narration**:
> "Simply upload a JSON file containing wall line segments. The system processes the floorplan in real-time."

**Key Points**:
- Show the file selection dialog
- Highlight the loading spinner
- Emphasize speed

---

### Step 2: Room Detection Results (0:30 - 0:45)
**Visual**:
- Show detected rooms appearing on the canvas
- Highlight the metrics display card
- Zoom in to show room bounding boxes

**Narration**:
> "In under a second, the system detects all rooms and displays them with bounding boxes. Notice the metrics showing processing time, room count, and confidence score."

**Key Points**:
- Show all rooms detected (20 or 50 rooms)
- Highlight metrics: processing time (< 1 second), confidence score (high)
- Show green bounding boxes for detected rooms
- Point out room labels

---

### Step 3: Room Interaction - Selection (0:45 - 1:00)
**Visual**:
- Click on a room in the canvas
- Show the room highlighting (orange border)
- Show the selected room info panel with action buttons

**Narration**:
> "Click any room to select it. The room is highlighted in orange, and you can see action buttons appear below the visualization."

**Key Points**:
- Demonstrate click interaction
- Show visual feedback (color change)
- Highlight the selected room name display

---

### Step 4: Room Renaming (1:00 - 1:20)
**Visual**:
- Click the edit/rename button
- Show the rename dialog opening
- Type a new name (e.g., "Living Room")
- Click Save
- Show the name updating on the canvas

**Narration**:
> "You can rename any room by clicking the edit button. Enter a custom name, and it updates immediately on the floorplan."

**Key Points**:
- Show Material UI dialog
- Demonstrate keyboard input
- Show real-time update on canvas
- Emphasize ease of use

---

### Step 5: Room Removal (1:20 - 1:35)
**Visual**:
- Click the delete button
- Show the room disappearing from the canvas
- Show metrics updating (room count decreases)

**Narration**:
> "If a detection is incorrect, simply click delete to remove it. The metrics automatically update to reflect the change."

**Key Points**:
- Show instant removal
- Highlight metrics update
- Demonstrate error correction capability

---

### Step 6: Multi-Room Detection (1:35 - 2:00)
**Visual**:
- Upload a different floorplan (e.g., `complex_floorplan.json` with 4 rooms)
- Show multiple rooms being detected
- Click through different rooms
- Show all rooms properly identified

**Narration**:
> "The system handles complex floorplans with multiple rooms, including those with internal walls and T-junctions. All rooms are detected accurately."

**Key Points**:
- Show complex floorplan
- Demonstrate multi-room detection
- Highlight accuracy
- Show face-finding algorithm working

---

### Step 7: Observability Features (2:00 - 2:15)
**Visual**:
- Focus on the metrics display card
- Show processing time, confidence score, room count
- Highlight color-coded confidence (green = high confidence)

**Narration**:
> "The system provides full observability with processing metrics and confidence scores, helping you understand the quality of detections."

**Key Points**:
- Show all three metrics clearly
- Explain confidence scoring
- Emphasize transparency

---

### Conclusion (2:15 - 2:30)
**Visual**:
- Show the complete interface
- Highlight key features with callouts
- Show before/after comparison (if possible)

**Narration**:
> "Room Detection AI transforms manual tracing into an automated, interactive experience. What used to take 5-15 minutes now takes under 3 seconds, and you review results instead of drawing them from scratch."

**Key Points**:
- Summarize benefits
- Emphasize time savings
- Highlight user experience improvement
- Call to action (if applicable)

---

## Technical Requirements

### Screen Recording Settings
- **Resolution**: 1920x1080 (Full HD) minimum
- **Frame Rate**: 30 FPS minimum
- **Format**: MP4 (H.264)
- **Audio**: Clear narration or background music with text overlays

### Application Setup
1. Start backend server: `cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000`
2. Start frontend: `cd frontend && npm start`
3. Have test files ready:
   - `tests/sample_data/20_connected_rooms/20_connected_rooms_floorplan.json`
   - `tests/sample_data/50_rooms/50_rooms_floorplan.json`
   - `tests/sample_data/complex/complex_floorplan.json`

### Recording Tips
- Use a clean browser window (no bookmarks bar, minimal extensions)
- Zoom browser to 100% for best quality
- Use smooth mouse movements
- Pause briefly at key moments for emphasis
- Consider adding text overlays for key features
- Use cursor highlighting if available in screen recorder

---

## Key Features to Highlight

1. **Speed**: Processing time < 1 second
2. **Accuracy**: Detects all rooms correctly (20, 50, or complex layouts)
3. **Interactivity**: Click to select, rename, remove
4. **Observability**: Real-time metrics and confidence scores
5. **User Experience**: Clean Material UI, intuitive controls
6. **Multi-Room Support**: Handles complex floorplans with internal walls

---

## Before/After Comparison

### Before (Manual Process)
- 40-100 clicks required
- 5-15 minutes setup time
- Requires CAD skills
- Inconsistent results
- Error-prone

### After (With Room Detection AI)
- Zero drawing required
- < 5 seconds processing
- No training needed
- Deterministic results
- Review and refine, not create from scratch

---

## Video Editing Suggestions

1. **Add Text Overlays**:
   - "Processing Time: 0.5 seconds"
   - "20 Rooms Detected"
   - "Confidence: 95%"
   - "Click to Select"
   - "Rename Room"

2. **Add Highlights**:
   - Circle or arrow pointing to key UI elements
   - Slow motion for room detection animation
   - Zoom in on metrics display

3. **Add Transitions**:
   - Smooth fade between sections
   - Wipe transitions for before/after comparisons

4. **Background Music**:
   - Light, professional background music (optional)
   - Ensure narration is clear and audible

---

## Deliverables Checklist

- [ ] Recorded video file (MP4 format)
- [ ] Video demonstrates all key features
- [ ] Video is 2-3 minutes in length
- [ ] Audio/narration is clear
- [ ] Video shows complete workflow
- [ ] Video highlights time savings
- [ ] Video demonstrates multi-room detection
- [ ] Video shows interaction features (rename, remove)
- [ ] Video displays observability metrics

---

## Post-Production Notes

After recording, review the video for:
- Clarity of demonstration
- Completeness of feature coverage
- Alignment with product goals
- Professional appearance
- Smooth transitions
- Clear audio/narration

