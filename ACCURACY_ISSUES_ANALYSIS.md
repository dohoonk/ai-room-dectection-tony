# Accuracy Issues Analysis

## Overview

This document tracks accuracy issues with the current room detection approach and plans for improvement using SageMaker training.

---

## 🔍 Current Accuracy Issues

### Questions to Answer

To help diagnose and fix accuracy issues, please provide:

1. **What specific problems are you seeing?**
   - [ ] Missing rooms (rooms not detected)
   - [ ] False positives (detecting rooms that don't exist)
   - [ ] Incorrect boundaries (wrong room shapes/sizes)
   - [ ] Wrong room counts
   - [ ] Other: _______________

2. **Which image types fail?**
   - [ ] Scanned blueprints (raster images)
   - [ ] PDF vector graphics
   - [ ] Hand-drawn sketches
   - [ ] Complex multi-room layouts
   - [ ] Simple single-room layouts
   - [ ] Other: _______________

3. **What's the failure rate?**
   - Out of 50 images, how many fail?
   - What percentage accuracy are you seeing?

4. **Example failures:**
   - Can you share 2-3 example images that fail?
   - What should the correct output be?
   - What is the current (incorrect) output?

---

## 🔧 Current Approach Limitations

### Image Processing Pipeline

**Current Flow:**
```
Image → OpenCV Preprocessing → Edge Detection (Canny) → Line Detection (Hough) → Line Filtering → Room Detection
```

**Potential Issues:**

1. **Edge Detection (Canny)**
   - May miss faint wall lines
   - May detect non-wall lines (furniture, text, etc.)
   - Sensitive to image quality and contrast

2. **Line Detection (Hough Transform)**
   - May miss diagonal or curved walls
   - May break continuous walls into segments
   - May detect spurious lines

3. **Line Filtering**
   - May filter out valid walls
   - May keep invalid lines
   - Orientation filtering may miss angled walls

4. **Room Detection**
   - Works well when wall segments are accurate
   - Fails when wall segments are incomplete or incorrect

---

## 🎯 SageMaker Training Benefits

### What SageMaker Can Improve

1. **Better Line Detection**
   - Learn architectural-specific patterns
   - Distinguish walls from furniture/text
   - Handle various image qualities

2. **Robust to Image Variations**
   - Different scanning qualities
   - Different drawing styles
   - Different scales and orientations

3. **Specialized for Floor Plans**
   - Understand architectural conventions
   - Recognize room boundaries
   - Handle complex layouts

---

## 📋 Diagnostic Steps

### Step 1: Identify Failure Patterns

Run current algorithm on your 50 images and document:

```python
# Diagnostic script
import json
from pathlib import Path

results = []

for image_path in Path('your_images/').glob('*.png'):
    # Run current detection
    rooms = detect_rooms_from_image(image_path)
    
    # Compare with ground truth
    expected = load_ground_truth(image_path)
    
    results.append({
        'image': image_path.name,
        'detected': len(rooms),
        'expected': len(expected['rooms']),
        'accuracy': calculate_accuracy(rooms, expected),
        'issues': identify_issues(rooms, expected)
    })

# Analyze patterns
analyze_failure_patterns(results)
```

### Step 2: Visualize Failures

Create visualizations showing:
- Input image
- Detected wall segments (overlay)
- Detected rooms (overlay)
- Ground truth (overlay)
- Differences highlighted

### Step 3: Categorize Issues

Group failures by type:
- **Type A**: Missing walls → Missing rooms
- **Type B**: Extra walls → False positive rooms
- **Type C**: Broken walls → Incomplete rooms
- **Type D**: Wrong wall angles → Wrong room shapes

---

## 🚀 SageMaker Training Plan

### Training Data Requirements

For each of your 50 images, you need:

1. **Image file** (PNG/JPG)
2. **Annotation file** (JSON) with:
   - Wall segments (start/end coordinates)
   - Room boundaries (optional, for validation)

### Annotation Format

```json
{
  "image_id": "floorplan_001",
  "walls": [
    {
      "start": [100, 100],
      "end": [500, 100],
      "is_load_bearing": false
    }
  ],
  "rooms": [
    {
      "id": "room_001",
      "bounding_box": [50, 50, 200, 300],
      "name_hint": "Bedroom"
    }
  ]
}
```

### Training Approach

1. **Use Transfer Learning**
   - Start with pre-trained U-Net (ImageNet weights)
   - Fine-tune on your 50 images
   - Heavy data augmentation (40 → 200-400 images)

2. **Focus on Problem Areas**
   - If missing walls: Emphasize wall detection
   - If false positives: Emphasize filtering
   - If wrong shapes: Emphasize precision

---

## 📝 Next Steps

1. **Document Issues**
   - Run diagnostic script on your 50 images
   - Categorize failure types
   - Identify common patterns

2. **Prepare Annotations**
   - Use `scripts/prepare_training_data.py` to organize images
   - Create annotations (manual or semi-automated)
   - Validate annotations

3. **Train Model**
   - Follow `SAGEMAKER_50_IMAGES_PLAN.md`
   - Use transfer learning
   - Monitor validation metrics

4. **Evaluate**
   - Test on held-out test set
   - Compare with current approach
   - Measure improvement

---

## 💡 Alternative: Hybrid Approach

Instead of replacing the current approach entirely, consider:

1. **Use SageMaker for difficult cases**
   - Detect when current approach fails (low confidence)
   - Fall back to SageMaker for those cases
   - Use current approach for easy cases (faster, cheaper)

2. **Use SageMaker to improve preprocessing**
   - Use SageMaker to filter/clean detected lines
   - Use current algorithm for room detection
   - Best of both worlds

---

**Last Updated:** 2025-11-09
**Status:** Awaiting User Input on Specific Issues

