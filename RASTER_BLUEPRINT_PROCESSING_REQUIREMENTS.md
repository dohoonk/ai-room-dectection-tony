# Processing Raster Blueprint Images: Requirements Analysis

## Input Analysis

**Input Type:** Raster image (PNG/JPG) of architectural floorplan
**Complexity:** High - Contains multiple elements:
- ✅ Walls (thick blue lines)
- ✅ Dimensions (thin lines with numbers)
- ✅ Doors (gaps with arcs)
- ✅ Windows (gaps with parallel lines)
- ✅ Stairs (parallel lines with arrow)
- ✅ Grid/axes labels (A, B, C / 1, 2, 3)
- ✅ Numerical labels (measurements, areas)
- ✅ Multiple rooms (5-7 distinct spaces)

## What You Need to Process This

### 1. **Frontend: Image Upload Component**

**New Component:** `ImageUpload.tsx` (or extend `FileUpload.tsx`)

**Requirements:**
```typescript
// Accept image files
const acceptedTypes = ['image/png', 'image/jpeg', 'image/jpg'];

// Handle image preview
const [imagePreview, setImagePreview] = useState<string | null>(null);

// Upload to backend
const handleImageUpload = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  // Call new endpoint
  const response = await fetch('/detect-rooms-from-image', {
    method: 'POST',
    body: formData
  });
};
```

**Changes Needed:**
- ✅ Accept image files (not just JSON)
- ✅ Show image preview
- ✅ Display original image as background in visualization
- ✅ Handle async processing (AWS services take time)

---

### 2. **Backend: New API Endpoint**

**New Endpoint:** `POST /detect-rooms-from-image`

**Requirements:**
```python
@app.post("/detect-rooms-from-image")
async def detect_rooms_from_image(
    file: UploadFile = File(...),
    canny_low: int = 50,
    canny_high: int = 150,
    hough_threshold: int = 100,
    min_line_length: int = 50
):
    """
    Process raster image blueprint to detect rooms.
    
    Steps:
    1. Upload image to S3 (AWS requirement)
    2. Call AWS services (Textract, Rekognition, SageMaker)
    3. Extract wall lines
    4. Convert to wall segments
    5. Use our algorithm to detect rooms
    """
    pass
```

**Changes Needed:**
- ✅ Accept multipart/form-data with image file
- ✅ Upload to S3 (AWS requirement)
- ✅ Integrate AWS services
- ✅ Process responses
- ✅ Return rooms in PRD format

---

### 3. **AWS Services Integration (Mandatory)**

#### 3.1 **Amazon S3** (File Storage)
**Purpose:** Store uploaded images (AWS requirement)

```python
# Upload image to S3
s3_client.upload_fileobj(
    file.file,
    bucket_name,
    s3_key,
    ExtraArgs={'ContentType': file.content_type}
)
```

**Required:**
- ✅ S3 bucket configuration
- ✅ IAM roles for S3 access
- ✅ CORS configuration

---

#### 3.2 **Amazon Textract** (OCR - Optional but Recommended)
**Purpose:** Extract text labels (room names, dimensions)

**What it can extract:**
- ✅ Room labels ("Kitchen", "Bedroom")
- ✅ Dimension numbers ("1400", "5500")
- ✅ Grid labels ("A", "B", "C", "1", "2", "3")

**What it CANNOT extract:**
- ❌ Wall line coordinates
- ❌ Geometric structure

**Implementation:**
```python
# Extract text from image
textract_response = textract.detect_document_text(
    Document={'S3Object': {'Bucket': bucket, 'Name': s3_key}}
)

# Parse room labels
room_labels = extract_room_names(textract_response)
```

**Value:** High - Auto-populate `name_hint` field (Phase 2C)

---

#### 3.3 **Amazon Rekognition** (Object Detection - Optional)
**Purpose:** Detect architectural elements

**What it can detect:**
- ✅ Doors (if trained with Custom Labels)
- ✅ Windows (if trained with Custom Labels)
- ✅ General objects

**What it CANNOT detect:**
- ❌ Wall lines directly
- ❌ Room boundaries

**Implementation:**
```python
# Detect objects
rekognition_response = rekognition.detect_labels(
    Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}}
)

# Filter architectural elements
architectural_objects = filter_architectural_elements(rekognition_response)
```

**Value:** Medium - Enhancement, not core functionality

---

#### 3.4 **Amazon SageMaker** (Custom Model - Likely Required)
**Purpose:** Extract wall line segments from raster image

**Why it's needed:**
- Textract: Extracts text, not geometry
- Rekognition: Detects objects, not lines
- **No AWS service extracts line coordinates directly**

**What you need to build:**
```python
# Custom SageMaker model
# Input: Raster image (PNG/JPG)
# Output: Wall line segments with coordinates

# Training data needed:
# - 1000+ labeled floorplan images
# - Each labeled with wall line coordinates
# - Various architectural styles
```

**Model Architecture (Example):**
- Convolutional Neural Network (CNN)
- Or Transformer-based model (ViT)
- Trained to detect straight lines (walls)
- Output: List of line segments `[{start: [x1, y1], end: [x2, y2]}, ...]`

**Implementation:**
```python
# Call SageMaker endpoint
response = sagemaker_client.invoke_endpoint(
    EndpointName='wall-line-extraction-model',
    ContentType='image/jpeg',
    Body=image_bytes
)

# Parse response
wall_segments = parse_sagemaker_response(response)
```

**Value:** Critical - If AWS services are mandatory, this is likely required

**Challenges:**
- ❌ Requires training data (1000s of labeled images)
- ❌ Model development (weeks/months)
- ❌ Ongoing maintenance
- ❌ Cost: ~$0.10-1.00 per inference

---

### 4. **Alternative: OpenCV (If Allowed)**

**If AWS requirement allows hybrid approach:**

**What you need:**
```python
# Image preprocessing
import cv2
import numpy as np

# Load image
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Edge detection
edges = cv2.Canny(gray, canny_low, canny_high)

# Line detection
lines = cv2.HoughLinesP(
    edges,
    rho=1,
    theta=np.pi/180,
    threshold=hough_threshold,
    minLineLength=min_line_length,
    maxLineGap=10
)

# Filter wall lines (thick, long lines)
wall_lines = filter_wall_lines(lines, image)

# Convert to wall segments
wall_segments = convert_to_segments(wall_lines)
```

**Value:** High - Fast, accurate, no training needed

**Compliance:** ⚠️ Depends on requirement interpretation

---

### 5. **Post-Processing Layer**

**Purpose:** Convert AWS/OpenCV output to our format

**Required Functions:**
```python
def process_aws_responses(textract_result, rekognition_result, sagemaker_result):
    """
    Combine AWS service responses into wall segments.
    """
    # Parse SageMaker output (wall lines)
    wall_segments = parse_sagemaker_lines(sagemaker_result)
    
    # Filter using Rekognition (remove non-wall objects)
    wall_segments = filter_with_rekognition(wall_segments, rekognition_result)
    
    # Add room labels from Textract
    room_labels = extract_room_labels(textract_result)
    
    return wall_segments, room_labels

def convert_to_wall_segments(detected_lines):
    """
    Convert detected lines to WallSegment format.
    """
    segments = []
    for line in detected_lines:
        segments.append(WallSegment(
            type="line",
            start=[line['x1'], line['y1']],
            end=[line['x2'], line['y2']],
            is_load_bearing=False  # Not detectable from raster
        ))
    return segments
```

**Required:**
- ✅ Parse SageMaker/OpenCV output
- ✅ Filter non-wall lines (dimensions, annotations)
- ✅ Coordinate transformation (image pixels → 0-1000 range)
- ✅ Validation (ensure segments form valid graph)

---

### 6. **Core Room Detection Algorithm (Existing)**

**Good News:** Our existing algorithm works!

**What you need:**
```python
# After extracting wall segments
from src.room_detector import detect_rooms

# Use existing algorithm
rooms = detect_rooms(wall_segments_json_path, tolerance=1.0)
```

**No changes needed** - Our algorithm already handles:
- ✅ Multiple rooms
- ✅ Complex layouts
- ✅ T-junctions
- ✅ Irregular shapes

---

### 7. **Frontend: Enhanced Visualization**

**Changes to `WallVisualization.tsx`:**

```typescript
// Display original image as background
<canvas
  ref={canvasRef}
  style={{
    backgroundImage: `url(${imageUrl})`, // Original blueprint image
    backgroundSize: 'contain',
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'center'
  }}
/>

// Draw detected rooms on top
rooms.forEach(room => {
  // Draw bounding box overlay
  ctx.strokeRect(...room.bounding_box);
});
```

**Required:**
- ✅ Display original image as background
- ✅ Overlay detected rooms
- ✅ Show room labels from Textract
- ✅ Handle image scaling/zooming

---

## Implementation Roadmap

### Phase 1: Basic Image Processing (If OpenCV Allowed)

**Tasks:**
1. ✅ Create `ImageUpload.tsx` component
2. ✅ Create `/detect-rooms-from-image` endpoint
3. ✅ Implement OpenCV line detection
4. ✅ Convert lines to wall segments
5. ✅ Use existing room detection algorithm
6. ✅ Update visualization to show image background

**Timeline:** 2-3 weeks
**Complexity:** Medium

---

### Phase 2: AWS Integration (If Required)

**Tasks:**
1. ✅ Set up S3 bucket
2. ✅ Integrate Textract (OCR)
3. ✅ Integrate Rekognition (optional)
4. ✅ Train SageMaker model (if required)
5. ✅ Deploy SageMaker endpoint
6. ✅ Process AWS responses
7. ✅ Combine with our algorithm

**Timeline:** 4-8 weeks (depending on SageMaker model)
**Complexity:** High

---

## Challenges for This Specific Image

### 1. **Filtering Non-Wall Lines**
**Problem:** Image has many lines:
- Walls (thick blue lines) ✅ Need these
- Dimensions (thin lines with numbers) ❌ Don't need
- Grid lines (axes) ❌ Don't need
- Annotations ❌ Don't need

**Solution:**
- Filter by line thickness (walls are thicker)
- Filter by length (walls are longer)
- Filter by color (if possible)
- Use Rekognition to identify non-wall elements

---

### 2. **Coordinate System**
**Problem:** Image has dimensions in millimeters (e.g., "1400", "5500")
**Solution:**
- Extract scale from dimension labels (Textract)
- Map image pixels to real-world coordinates
- Normalize to 0-1000 range

---

### 3. **Multiple Elements**
**Problem:** Doors, windows, stairs complicate detection
**Solution:**
- Use Rekognition to identify these elements
- Filter them out from wall detection
- Or use them to enhance room detection

---

### 4. **Image Quality**
**Problem:** Raster images can vary in quality
**Solution:**
- Image preprocessing (grayscale, noise reduction)
- Adaptive thresholds
- Parameter tuning interface

---

## Recommended Approach

### Option A: Hybrid (If Allowed)
```
Image → S3
  ↓
Parallel:
  ├─ Textract → Room labels (OCR)
  ├─ Rekognition → Objects (doors, windows)
  └─ OpenCV → Wall lines (our algorithm)
  ↓
Combine → Wall Segments
  ↓
Our Algorithm → Rooms
```

**Pros:**
- ✅ Fast (< 1 second)
- ✅ Accurate (proven)
- ✅ Uses AWS services (compliance)
- ✅ Lower cost

---

### Option B: Full AWS (If Required)
```
Image → S3
  ↓
Parallel:
  ├─ Textract → Room labels
  ├─ Rekognition → Objects
  └─ SageMaker → Wall lines (custom model)
  ↓
Combine → Wall Segments
  ↓
Our Algorithm → Rooms
```

**Pros:**
- ✅ Fully AWS-native
- ✅ Complies with requirement

**Cons:**
- ❌ Requires SageMaker model training
- ❌ Slower (10-60 seconds)
- ❌ Higher cost
- ❌ More complex

---

## Summary: What You Need

### Minimum Requirements:
1. ✅ **Frontend:** Image upload component
2. ✅ **Backend:** New API endpoint
3. ✅ **S3:** File storage (AWS requirement)
4. ✅ **Line Detection:** SageMaker model OR OpenCV (if allowed)
5. ✅ **OCR:** Textract (for room labels)
6. ✅ **Post-Processing:** Convert to wall segments
7. ✅ **Room Detection:** Our existing algorithm
8. ✅ **Visualization:** Display image + detected rooms

### If AWS Services Mandatory:
- **SageMaker model** for line extraction (biggest requirement)
- **Training data** (1000s of labeled floorplans)
- **Model development** (weeks/months)

### If Hybrid Allowed:
- **OpenCV** for line extraction (faster, easier)
- **Textract** for OCR (room labels)
- **Our algorithm** for room detection

**Bottom Line:** The biggest challenge is extracting wall lines from raster images. If AWS services are mandatory, you'll need a custom SageMaker model. If hybrid is allowed, OpenCV + Textract + our algorithm is the best approach.

