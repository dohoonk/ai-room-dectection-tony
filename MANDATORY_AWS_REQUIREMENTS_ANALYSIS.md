# Mandatory AWS Requirements Analysis

## Requirement Breakdown

### 4.1 Technical Stack

**Cloud Platform: AWS (Mandatory)**
- ✅ Must use AWS as the cloud platform
- ❌ Cannot use other cloud providers (Azure, GCP, etc.)
- ❌ Cannot be purely local/on-premise

**AI Frameworks: AWS AI/ML Services (Mandatory)**
- ✅ Must use AWS AI/ML services:
  - Amazon Textract (document processing)
  - Amazon SageMaker (ML model training/deployment)
  - AWS Computer Vision services (likely Rekognition or custom)
- ❌ Cannot use standalone libraries (PyMuPDF, OpenCV) without AWS integration
- ❌ Must integrate "document processing capabilities similar to DocumentAI"

**Development Tools:**
- React (Front-end) ✅ Already using
- Visual Studio Code / Visual Studio (Back-end) ✅ Already using

## What This Means

### 1. **AWS is Mandatory (Not Optional)**
- Cannot deploy to other cloud platforms
- Must use AWS infrastructure (S3, Lambda, ECS, etc.)
- Local MVP is fine for development, but production must be AWS

### 2. **AWS AI/ML Services are Mandatory (Not Optional)**
- **Cannot use PyMuPDF alone** - must integrate with AWS services
- **Cannot use OpenCV alone** - must integrate with AWS services
- Must use AWS AI/ML services for document processing

### 3. **DocumentAI-like Capabilities Required**
- Google DocumentAI is a document understanding service
- AWS equivalent would be:
  - **Textract** for text/forms/tables extraction
  - **Custom SageMaker model** for specialized document understanding
  - **Rekognition** for computer vision tasks

## Implications for Our Current Plan

### ❌ **Current Plan (Phase 2A/2B) is NOT Compliant**

**What We Planned:**
```
PDF/Image → PyMuPDF/OpenCV → Our Algorithm → Rooms
```

**What's Required:**
```
PDF/Image → AWS Services (Textract/SageMaker/Rekognition) → Our Algorithm → Rooms
```

### ✅ **What We Need to Change**

#### Phase 2A: PDF Vector Extraction
**Current Plan:**
- Use PyMuPDF directly
- Extract vector paths
- Process locally

**Required (Compliant):**
- Upload PDF to S3
- Use **Textract** for document analysis
- Use **SageMaker** custom model (if needed) for vector extraction
- Process Textract/SageMaker responses
- Use our algorithm for room detection

#### Phase 2B: Raster Image Processing
**Current Plan:**
- Use OpenCV directly
- Edge detection, line detection
- Process locally

**Required (Compliant):**
- Upload image to S3
- Use **Rekognition** for computer vision
- Use **SageMaker** custom model for line detection
- Process Rekognition/SageMaker responses
- Use our algorithm for room detection

## How to Make It Compliant

### Option 1: Hybrid Approach (Recommended)
**Use AWS services where required, but keep our algorithm:**

```
PDF/Image → S3
  ↓
AWS Services:
  ├─ Textract → Extract text, forms, tables
  ├─ Rekognition → Detect objects, labels
  └─ SageMaker → Custom model for line/vector extraction
  ↓
Process AWS Responses → WallSegment[]
  ↓
Our Algorithm (NetworkX + Shapely) → Rooms
```

**Benefits:**
- ✅ Complies with AWS requirement
- ✅ Keeps our proven algorithm
- ✅ Uses AWS services for extraction
- ✅ Best of both worlds

### Option 2: Full AWS (More Complex)
**Train custom SageMaker model for room detection:**

```
PDF/Image → S3
  ↓
AWS Services:
  ├─ Textract → Extract text, forms
  ├─ Rekognition → Detect objects
  └─ SageMaker → Custom model for:
      ├─ Line extraction
      └─ Room detection
  ↓
Return Rooms
```

**Challenges:**
- ❌ Requires training data
- ❌ Model development and deployment
- ❌ Ongoing maintenance
- ❌ Higher costs

## Required Changes to Our Plan

### 1. **Update Phase 2A (PDF Extraction)**

**Add:**
- S3 integration for PDF storage
- Textract integration for document analysis
- SageMaker custom model for vector extraction (if Textract insufficient)
- AWS response processing layer

**Keep:**
- Our room detection algorithm (NetworkX + Shapely)

### 2. **Update Phase 2B (Raster Image)**

**Add:**
- S3 integration for image storage
- Rekognition integration for computer vision
- SageMaker custom model for line detection (if Rekognition insufficient)
- AWS response processing layer

**Keep:**
- Our room detection algorithm (NetworkX + Shapely)

### 3. **Update Infrastructure Plan**

**Add:**
- S3 buckets (mandatory)
- SageMaker endpoint (for custom models)
- Textract service access
- Rekognition service access
- IAM roles for service access

## Cost Implications

### AWS Service Costs (Per 1000 Requests)

| Service | Cost | Usage |
|---------|------|-------|
| **Textract** | $15-50 | PDF document analysis |
| **Rekognition** | $1-5 | Image analysis |
| **SageMaker** | $0.10-1.00/inference | Custom model inference |
| **S3** | $0.023/GB | File storage |
| **Total** | **~$16-56** | Per 1000 requests |

**At scale:** Could be expensive, but required by mandate.

## Architecture Compliance Check

### ✅ Compliant Architecture:

```
User → React Frontend
  ↓ (uploads PDF/Image)
FastAPI Backend
  ↓
Upload to S3
  ↓
AWS Services:
  ├─ Textract (PDF analysis)
  ├─ Rekognition (Image analysis)
  └─ SageMaker (Custom model for line extraction)
  ↓
Process AWS Responses → WallSegment[]
  ↓
Our Algorithm (NetworkX + Shapely) → Rooms
  ↓
Return JSON: Room[]
```

### ❌ Non-Compliant Architecture:

```
User → React Frontend
  ↓ (uploads PDF/Image)
FastAPI Backend
  ↓
PyMuPDF/OpenCV (direct processing)
  ↓
Our Algorithm → Rooms
```

## Next Steps

1. **Confirm Requirement Source**
   - Is this from a client/stakeholder?
   - Is this a new constraint?
   - Can we get clarification on scope?

2. **Update PRD**
   - Add mandatory AWS requirements section
   - Update Phase 2A/2B to include AWS services
   - Update technical architecture

3. **Update Tasks**
   - Modify Task 20 (PDF Extraction) to include AWS services
   - Modify Task 21 (Raster Image) to include AWS services
   - Add new subtasks for AWS integration

4. **Update Implementation Plan**
   - Add AWS SDK setup
   - Add S3 integration
   - Add Textract/Rekognition/SageMaker integration
   - Add response processing layer

## Questions to Clarify

1. **Scope of AWS Requirement:**
   - Must ALL processing use AWS services?
   - Or can we use AWS for extraction, our algorithm for detection?

2. **SageMaker Model:**
   - Do we need to train a custom model?
   - Or can we use pre-trained AWS services?

3. **DocumentAI Equivalence:**
   - What specific DocumentAI capabilities are required?
   - Text extraction? Form parsing? Layout analysis?

4. **Timeline:**
   - Is this required for MVP or Phase 2?
   - Can MVP be local, Phase 2 be AWS-compliant?

## Recommendation

**Adopt Hybrid Approach:**
- Use AWS services (Textract, Rekognition, SageMaker) for document/image processing
- Keep our proven algorithm (NetworkX + Shapely) for room detection
- This complies with requirements while maintaining our algorithm's performance

**Update Plan:**
- Phase 2A: PDF → S3 → Textract/SageMaker → Our Algorithm
- Phase 2B: Image → S3 → Rekognition/SageMaker → Our Algorithm

