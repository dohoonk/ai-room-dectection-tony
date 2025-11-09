# AWS Computer Vision Services Analysis for Room Detection

## AWS Computer Vision Services Overview

AWS offers several computer vision services. Let's analyze which ones could help with our room detection use case.

## Available AWS Computer Vision Services

### 1. **Amazon Rekognition**
**What it does:**
- Object detection (furniture, doors, windows)
- Label detection (general categories)
- Text detection (OCR)
- Face detection
- Custom labels (train custom models)

**For Our Use Case:**
- ✅ **Could detect objects** in floorplans (doors, windows, furniture)
- ✅ **Custom Labels** - Could train model to detect "wall" objects
- ❌ **No built-in line/edge detection** for architectural drawings
- ❌ **Doesn't understand floorplan geometry** (rooms, boundaries)

**Example Use:**
```python
# Detect objects in floorplan
response = rekognition.detect_labels(
    Image={'S3Object': {'Bucket': 'bucket', 'Name': 'floorplan.jpg'}}
)

# Returns: ["Door", "Window", "Furniture", etc.]
# But NOT: Wall lines, room boundaries
```

**Verdict:** ⚠️ **Limited help** - Can detect objects but not wall lines directly.

---

### 2. **Amazon Textract**
**What it does:**
- Extract text from documents
- Extract forms (key-value pairs)
- Extract tables
- Document analysis (layout, structure)

**For Our Use Case:**
- ✅ **Extract room labels** (e.g., "Kitchen", "Bedroom") - Phase 2C
- ✅ **Extract form fields** (if floorplan has structured data)
- ❌ **Cannot extract line coordinates** directly
- ❌ **Focuses on text, not geometry**

**Example Use:**
```python
# Extract text from floorplan
response = textract.detect_document_text(
    Document={'S3Object': {'Bucket': 'bucket', 'Name': 'floorplan.pdf'}}
)

# Returns: Text blocks with bounding boxes
# But NOT: Wall line segments
```

**Verdict:** ✅ **Helpful for OCR** (room labels) but not for line detection.

---

### 3. **Amazon Lookout for Vision**
**What it does:**
- Anomaly detection in images
- Quality control
- Defect detection

**For Our Use Case:**
- ❌ **Not relevant** - We're not detecting anomalies
- ❌ **Not designed for geometric analysis**

**Verdict:** ❌ **Not helpful** for our use case.

---

### 4. **Amazon Augmented AI (A2I)**
**What it does:**
- Human review of AI predictions
- Quality assurance
- Confidence thresholding

**For Our Use Case:**
- ✅ **Could use for human review** of detected rooms
- ✅ **Quality assurance** for room detection
- ⚠️ **Adds human-in-the-loop** (slower, more expensive)

**Example Use:**
```python
# If confidence < threshold, send to human review
if confidence < 0.8:
    a2i.start_human_loop(...)
```

**Verdict:** ⚠️ **Could help with quality** but adds complexity.

---

### 5. **Amazon SageMaker (Custom Models)**
**What it does:**
- Train custom ML models
- Deploy models as endpoints
- Computer vision models (CNNs, Transformers)

**For Our Use Case:**
- ✅ **Could train model** to detect wall lines
- ✅ **Could train model** to detect rooms directly
- ❌ **Requires training data** (1000s of labeled floorplans)
- ❌ **Requires model development** (weeks/months)

**Verdict:** ✅ **Most flexible** but requires significant effort.

---

## Can AWS Computer Vision Detect Wall Lines?

### Direct Answer: **No, not out-of-the-box**

**Why:**
1. **Rekognition** detects objects, not geometric lines
2. **Textract** extracts text, not coordinates
3. **No AWS service** has built-in architectural line detection

### Workaround: **Custom Model with SageMaker**

**Option 1: Train Custom Rekognition Model**
```python
# Use Rekognition Custom Labels
# Train model to detect "wall" objects
# But still doesn't give line coordinates
```

**Option 2: Train SageMaker Model**
```python
# Train CNN/Transformer model
# Input: Floorplan image
# Output: Wall line segments with coordinates
```

---

## What AWS Computer Vision CAN Help With

### ✅ **1. Object Detection (Rekognition)**
Detect architectural elements:
- Doors
- Windows
- Furniture
- Stairs
- Appliances

**Use Case:** Enhance room detection by identifying room features.

**Example:**
```python
# Detect objects
response = rekognition.detect_labels(
    Image={'S3Object': {'Bucket': 'bucket', 'Name': 'floorplan.jpg'}}
)

# Filter for architectural elements
architectural_elements = [
    label for label in response['Labels']
    if label['Name'] in ['Door', 'Window', 'Stairs']
]
```

### ✅ **2. Text Extraction (Textract)**
Extract room labels and annotations:
- Room names ("Kitchen", "Bedroom")
- Dimensions
- Notes

**Use Case:** Auto-populate `name_hint` field (Phase 2C).

**Example:**
```python
# Extract text
response = textract.detect_document_text(
    Document={'S3Object': {'Bucket': 'bucket', 'Name': 'floorplan.pdf'}}
)

# Find room labels
room_labels = extract_room_names(response)
```

### ✅ **3. Custom Line Detection (SageMaker)**
Train model to detect wall lines:
- Input: Floorplan image
- Output: Line segments with coordinates

**Use Case:** Replace PyMuPDF/OpenCV with AWS-native solution.

**Example:**
```python
# Call custom SageMaker endpoint
response = sagemaker.invoke_endpoint(
    EndpointName='wall-line-detection-model',
    Body=image_bytes
)

# Returns wall segments
wall_segments = json.loads(response['Body'].read())
```

---

## Comparison: AWS vs Our Current Approach

### Current Approach (PyMuPDF/OpenCV):
```
PDF/Image → PyMuPDF/OpenCV → Wall Segments → Our Algorithm → Rooms
```

**Pros:**
- ✅ Fast (< 1 second)
- ✅ Accurate (proven 100%)
- ✅ No training needed
- ✅ Low cost (free)

**Cons:**
- ❌ Not AWS-native
- ❌ Might not comply with requirement

### AWS Computer Vision Approach:
```
PDF/Image → S3 → Rekognition/Textract/SageMaker → Wall Segments → Our Algorithm → Rooms
```

**Pros:**
- ✅ AWS-native (compliance)
- ✅ Scalable (AWS infrastructure)
- ✅ Managed services

**Cons:**
- ❌ Slower (10-60 seconds)
- ❌ Higher cost ($16-56 per 1000 requests)
- ❌ Requires custom model training (SageMaker)
- ❌ More complex

---

## Recommended Hybrid Approach

### Use AWS Computer Vision Where It Adds Value:

```
PDF/Image → S3
  ↓
Parallel Processing:
  ├─ Textract → Extract room labels (OCR)
  ├─ Rekognition → Detect objects (doors, windows)
  └─ Our Algorithm (PyMuPDF/OpenCV) → Extract wall lines
  ↓
Combine Results:
  ├─ Wall segments (from our algorithm)
  ├─ Room labels (from Textract)
  └─ Objects (from Rekognition)
  ↓
Our Algorithm (NetworkX + Shapely) → Detect rooms
  ↓
Enhance with:
  ├─ Room labels (from Textract)
  └─ Objects (from Rekognition)
  ↓
Return Rooms
```

**Benefits:**
- ✅ Uses AWS services (compliance)
- ✅ Keeps our proven algorithms (performance)
- ✅ Adds value (OCR, object detection)
- ✅ Best of both worlds

---

## Specific Use Cases

### Use Case 1: Room Label Extraction (Textract)
**Problem:** Floorplans have room labels ("Kitchen", "Bedroom")

**Solution:**
```python
# Extract text with Textract
textract_response = textract.detect_document_text(
    Document={'S3Object': {'Bucket': bucket, 'Name': key}}
)

# Find room labels
room_labels = []
for block in textract_response['Blocks']:
    if block['BlockType'] == 'WORD':
        text = block['Text']
        # Check if it's a room name
        if is_room_name(text):
            room_labels.append({
                'name': text,
                'bbox': block['Geometry']['BoundingBox']
            })

# Match labels to detected rooms
matched_rooms = match_labels_to_rooms(rooms, room_labels)
```

**Result:** Auto-populate `name_hint` field.

---

### Use Case 2: Object Detection (Rekognition)
**Problem:** Want to identify room features (doors, windows)

**Solution:**
```python
# Detect objects
rekognition_response = rekognition.detect_labels(
    Image={'S3Object': {'Bucket': bucket, 'Name': key}}
)

# Filter architectural elements
architectural_objects = []
for label in rekognition_response['Labels']:
    if label['Name'] in ['Door', 'Window', 'Stairs']:
        architectural_objects.append({
            'type': label['Name'],
            'confidence': label['Confidence'],
            'bbox': label['Instances'][0]['BoundingBox']
        })

# Enhance room detection with object locations
enhanced_rooms = enhance_with_objects(rooms, architectural_objects)
```

**Result:** Better room identification (e.g., room with door = entrance).

---

### Use Case 3: Custom Line Detection (SageMaker)
**Problem:** Need to extract wall lines (if required for compliance)

**Solution:**
```python
# Train custom SageMaker model
# Input: Floorplan image
# Output: Wall line segments

# Deploy model
endpoint = sagemaker.deploy(
    model_name='wall-line-detection',
    initial_instance_count=1,
    instance_type='ml.m5.large'
)

# Use for inference
response = endpoint.predict(image_bytes)
wall_segments = parse_response(response)
```

**Result:** AWS-native line extraction (replaces PyMuPDF/OpenCV).

---

## Cost Analysis

### AWS Computer Vision Services (Per 1000 Requests):

| Service | Cost | Use Case |
|---------|------|----------|
| **Rekognition** | $1-5 | Object detection |
| **Textract** | $15-50 | Text extraction |
| **SageMaker** | $0.10-1.00 | Custom model inference |
| **A2I** | $0.08-0.20 | Human review |

**Total (if using all):** ~$16-56 per 1000 requests

**Our Current Approach:** Free (local processing)

---

## Verdict: Will AWS Computer Vision Help?

### ✅ **YES, for:**
1. **Room label extraction** (Textract) - Phase 2C
2. **Object detection** (Rekognition) - Enhancement
3. **Compliance** - Using AWS services

### ❌ **NO, for:**
1. **Direct wall line detection** - No built-in capability
2. **Room detection** - Would need custom SageMaker model
3. **Performance** - Slower than our current approach

### ⚠️ **MAYBE, for:**
1. **Custom line detection** - If we train SageMaker model
2. **Quality assurance** - A2I for human review

---

## Recommendation

### Use AWS Computer Vision Strategically:

1. **Textract** → Extract room labels (Phase 2C)
   - ✅ High value
   - ✅ Easy to implement
   - ✅ AWS-native

2. **Rekognition** → Detect objects (optional enhancement)
   - ✅ Adds value
   - ✅ Easy to implement
   - ⚠️ Not critical

3. **SageMaker** → Custom line detection (only if required)
   - ⚠️ Complex to implement
   - ⚠️ Requires training data
   - ⚠️ Only if mandate requires it

4. **Our Algorithms** → Core processing
   - ✅ Keep for line extraction
   - ✅ Keep for room detection
   - ✅ Proven performance

**Best Approach:**
```
AWS Services (Textract/Rekognition) + Our Algorithms (PyMuPDF/OpenCV/NetworkX)
= Compliance + Performance
```

