"""FastAPI backend server for Room Detection AI."""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import sys
import os
import tempfile
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))
from src.room_detector import detect_rooms
from src.pdf_parser import PDFParser
from src.pdf_validator import validate_pdf_segments
from src.image_validator import validate_image_segments
from src.parser import parse_line_segments
from src.parser import WallSegment as ParserWallSegment
from src.aws_s3 import S3Client
from src.aws_textract import TextractClient
from src.aws_rekognition import RekognitionClient
from src.image_preprocessor import ImagePreprocessor, PreprocessingConfig
from src.line_detector import LineDetector, EdgeDetectionConfig, LineDetectionConfig, LineDetectionParams
from src.line_filter import LineFilter, LineFilterConfig
import cv2
import numpy as np

app = FastAPI(title="Room Detection API", version="0.1.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WallSegment(BaseModel):
    """Wall segment input model."""
    type: str
    start: List[float]
    end: List[float]
    is_load_bearing: bool = False


class RoomDetectionRequest(BaseModel):
    """Request model for room detection."""
    walls: List[WallSegment]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Room Detection API is running!", "status": "ok"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/detect-rooms-from-pdf", response_model=List[Dict[str, Any]])
async def detect_rooms_from_pdf(
    file: UploadFile = File(...),
    use_textract: bool = False,
    use_rekognition: bool = False
):
    """
    Detect rooms from a PDF blueprint file.
    
    Processing pipeline:
    1. Upload PDF to S3
    2. (Optional) Call Textract and Rekognition in parallel
    3. Extract vector paths from PDF
    4. Transform coordinates to 0-1000 range
    5. Filter wall lines
    6. Convert to wall segments
    7. Validate segments
    8. Detect rooms using existing algorithm
    
    Args:
        file: PDF file upload
        use_textract: Whether to use Amazon Textract for OCR (optional)
        use_rekognition: Whether to use Amazon Rekognition for object detection (optional)
        
    Returns:
        List of detected rooms in PRD-compliant format
    """
    temp_file_path = None
    s3_object_key = None
    
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Initialize clients
        bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        if not bucket_name:
            raise HTTPException(status_code=500, detail="AWS_S3_BUCKET_NAME not configured")
        
        s3_client = S3Client(bucket_name=bucket_name)
        
        # Upload to S3
        print(f"📤 Uploading {file.filename} to S3...")
        s3_object_key = s3_client.upload_file(
            file_content=content,
            file_name=file.filename,
            content_type='application/pdf',
            folder='pdfs/'
        )
        print(f"✅ Uploaded to S3: {s3_object_key}")
        
        # Optional: Call AWS services in parallel
        textract_result = None
        rekognition_result = None
        
        if use_textract or use_rekognition:
            tasks = []
            if use_textract:
                textract_client = TextractClient()
                tasks.append(('textract', textract_client.detect_document_text(bucket_name, s3_object_key)))
            if use_rekognition:
                rekognition_client = RekognitionClient()
                tasks.append(('rekognition', rekognition_client.detect_labels(bucket_name, s3_object_key)))
            
            # Run AWS services (they're synchronous, but we can run them concurrently)
            if tasks:
                print(f"🔍 Running AWS services: {[t[0] for t in tasks]}")
                # For now, run sequentially (boto3 calls are blocking)
                for service_name, task in tasks:
                    try:
                        if service_name == 'textract':
                            textract_result = task
                            print(f"✅ Textract completed: {len(textract_result.get('lines', []))} lines detected")
                        elif service_name == 'rekognition':
                            rekognition_result = task
                            print(f"✅ Rekognition completed: {len(rekognition_result.get('labels', []))} labels detected")
                    except Exception as e:
                        print(f"⚠️  {service_name} error: {e}")
        
        # Extract lines from PDF
        print("📄 Extracting lines from PDF...")
        parser = PDFParser()
        doc = parser.open_pdf(temp_file_path)
        
        # Extract lines from all pages
        all_lines = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            lines = parser.extract_lines(page, page_number=page_num)
            all_lines.extend(lines)
        
        doc.close()
        print(f"✅ Extracted {len(all_lines)} lines from PDF")
        
        if not all_lines:
            raise HTTPException(status_code=400, detail="No lines found in PDF. Ensure PDF contains vector graphics.")
        
        # Transform coordinates to 0-1000 range
        print("🔄 Transforming coordinates...")
        normalized_lines = parser.transform_coordinates(all_lines)
        print(f"✅ Normalized {len(normalized_lines)} lines")
        
        # Filter wall lines
        print("🔍 Filtering wall lines...")
        filtered_lines = parser.filter_wall_lines(
            normalized_lines,
            min_thickness=2.0,
            max_thickness=10.0,
            min_length=10.0,
            preferred_colors=None  # Default to black
        )
        print(f"✅ Filtered to {len(filtered_lines)} wall lines")
        
        if not filtered_lines:
            raise HTTPException(status_code=400, detail="No wall lines found after filtering. Adjust filter parameters.")
        
        # Convert to wall segments
        print("🏗️  Converting to wall segments...")
        wall_segments_dict = parser.convert_to_wall_segments(filtered_lines, normalize=True)
        
        # Convert to WallSegment objects for validation
        # Use ParserWallSegment (simple class, not Pydantic model)
        wall_segments = [
            ParserWallSegment(
                start=(seg['start'][0], seg['start'][1]),
                end=(seg['end'][0], seg['end'][1]),
                is_load_bearing=seg.get('is_load_bearing', False)
            )
            for seg in wall_segments_dict
        ]
        
        # Validate segments (with relaxed connectivity check for PDFs)
        print("✅ Validating segments...")
        # For PDF-extracted segments, use non-strict mode and allow higher isolated ratio
        # since endpoints may need snapping tolerance applied
        validation_result = validate_pdf_segments(wall_segments, strict=False)
        
        if not validation_result['valid']:
            warnings = validation_result.get('warnings', [])
            errors = validation_result.get('errors', [])
            if errors:
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation failed: {'; '.join(errors)}"
                )
            if warnings:
                print(f"⚠️  Validation warnings: {'; '.join(warnings)}")
        
        # Detect rooms using existing algorithm
        print("🔍 Detecting rooms...")
        # Convert wall segments to temporary JSON for detect_rooms function
        import json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            walls_data = [
                {
                    "type": "line",
                    "start": [seg.start[0], seg.start[1]],
                    "end": [seg.end[0], seg.end[1]],
                    "is_load_bearing": seg.is_load_bearing
                }
                for seg in wall_segments
            ]
            json.dump(walls_data, f)
            temp_json_path = f.name
        
        try:
            # Use higher tolerance for PDF-extracted segments (matching validator)
            # PDF coordinates may have precision issues after normalization
            rooms = detect_rooms(temp_json_path, tolerance=5.0)
            print(f"✅ Detected {len(rooms)} rooms")
        finally:
            if os.path.exists(temp_json_path):
                os.unlink(temp_json_path)
        
        # Convert to PRD-compliant format (remove confidence, ensure array format)
        prd_compliant_rooms = []
        for room in rooms:
            prd_compliant_rooms.append({
                "id": room["id"],
                "bounding_box": room["bounding_box"],
                "name_hint": room.get("name_hint", "")
            })
        
        return prd_compliant_rooms
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        # Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@app.post("/detect-rooms-from-image", response_model=List[Dict[str, Any]])
async def detect_rooms_from_image(
    file: UploadFile = File(...),
    use_textract: bool = Form(False),
    use_rekognition: bool = Form(False),
    parameters: Optional[str] = Form(None)  # JSON string of ImageProcessingParameters
):
    """
    Detect rooms from a raster image blueprint file (PNG, JPG, etc.).
    
    Processing pipeline:
    1. Upload image to S3
    2. (Optional) Call Textract and Rekognition in parallel
    3. Preprocess image (grayscale, noise reduction, contrast enhancement)
    4. Detect edges using Canny edge detection
    5. Detect lines using Hough line transform
    6. Filter lines (using Rekognition results if available)
    7. Convert to wall segments
    8. Validate segments
    9. Detect rooms using existing algorithm
    
    Args:
        file: Image file upload (PNG, JPG, etc.)
        use_textract: Whether to use Amazon Textract for OCR (optional)
        use_rekognition: Whether to use Amazon Rekognition for object detection (optional)
        
    Returns:
        List of detected rooms in PRD-compliant format
    """
    temp_file_path = None
    s3_object_key = None
    
    try:
        # Validate file type
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File must be an image ({', '.join(allowed_extensions)})"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Initialize clients
        bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        if not bucket_name:
            raise HTTPException(status_code=500, detail="AWS_S3_BUCKET_NAME not configured")
        
        s3_client = S3Client(bucket_name=bucket_name)
        
        # Upload to S3
        print(f"📤 Uploading {file.filename} to S3...")
        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        content_type = content_type_map.get(file_ext, 'image/png')
        s3_object_key = s3_client.upload_file(
            file_content=content,
            file_name=file.filename,
            content_type=content_type,
            folder='images/'
        )
        print(f"✅ Uploaded to S3: {s3_object_key}")
        
        # Optional: Call AWS services in parallel
        textract_result = None
        rekognition_result = None
        rekognition_client = None
        
        if use_textract or use_rekognition:
            tasks = []
            if use_textract:
                textract_client = TextractClient()
                tasks.append(('textract', textract_client.detect_document_text(bucket_name, s3_object_key)))
            if use_rekognition:
                rekognition_client = RekognitionClient()
                tasks.append(('rekognition', rekognition_client.detect_labels(bucket_name, s3_object_key)))
            
            # Run AWS services (they're synchronous, but we can run them concurrently)
            if tasks:
                print(f"🔍 Running AWS services: {[t[0] for t in tasks]}")
                # For now, run sequentially (boto3 calls are blocking)
                for service_name, task in tasks:
                    try:
                        if service_name == 'textract':
                            textract_result = task
                            print(f"✅ Textract completed: {len(textract_result.get('lines', []))} lines detected")
                        elif service_name == 'rekognition':
                            rekognition_result = task
                            print(f"✅ Rekognition completed: {len(rekognition_result.get('labels', []))} labels detected")
                    except Exception as e:
                        print(f"⚠️  {service_name} error: {e}")
        
        # Load image
        print("🖼️  Loading image...")
        image = cv2.imread(temp_file_path)
        if image is None:
            raise HTTPException(status_code=400, detail="Could not load image. Ensure file is a valid image.")
        
        image_height, image_width = image.shape[:2]
        print(f"✅ Loaded image: {image_width}x{image_height}")
        
        # Parse optional parameters
        params = None
        if parameters:
            try:
                params = json.loads(parameters)
            except json.JSONDecodeError:
                print("⚠️  Invalid parameters JSON, using defaults")
                params = None
        
        # Preprocess image with optional parameters
        print("🔧 Preprocessing image...")
        preprocessing_config = None
        if params:
            preprocessing_config = PreprocessingConfig(
                gaussian_blur_kernel_size=params.get('gaussianBlurKernelSize', 5),
                gaussian_blur_sigma=params.get('gaussianBlurSigma', 1.0),
                use_histogram_equalization=params.get('useHistogramEqualization', True)
            )
        preprocessor = ImagePreprocessor(config=preprocessing_config)
        preprocessed = preprocessor.preprocess(image)
        print(f"✅ Preprocessed image")
        
        # Detect edges and lines with optional parameters
        print("🔍 Detecting edges and lines...")
        line_detection_params = None
        if params:
            edge_config = EdgeDetectionConfig(
                low_threshold=params.get('cannyLowThreshold', 50),
                high_threshold=params.get('cannyHighThreshold', 150)
            )
            line_config = LineDetectionConfig(
                threshold=params.get('houghThreshold', 100),
                min_line_length=params.get('minLineLength', 50.0),
                max_line_gap=params.get('maxLineGap', 10.0)
            )
            line_detection_params = LineDetectionParams(
                edge_config=edge_config,
                line_config=line_config
            )
        line_detector = LineDetector(params=line_detection_params)
        lines = line_detector.detect_lines_from_image(preprocessed)
        print(f"✅ Detected {len(lines)} lines")
        
        if not lines:
            raise HTTPException(
                status_code=400, 
                detail="No lines detected in image. Try adjusting preprocessing or detection parameters."
            )
        
        # Filter lines with optional parameters
        print("🔍 Filtering lines...")
        filter_config = None
        if params:
            filter_config = LineFilterConfig(
                min_length=params.get('minLength', 20.0),
                angle_tolerance=params.get('angleTolerance', 5.0)
            )
        line_filter = LineFilter(config=filter_config)
        filtered_lines = line_filter.filter_lines(lines)
        print(f"✅ Filtered to {len(filtered_lines)} lines")
        
        # Use Rekognition results to filter out non-wall elements if available
        if use_rekognition and rekognition_result and rekognition_client:
            print("🔍 Using Rekognition results to filter lines...")
            # Get architectural elements (doors, windows) from Rekognition
            architectural_elements = rekognition_client.filter_architectural_elements(rekognition_result)
            if architectural_elements:
                print(f"⚠️  Found {len(architectural_elements)} architectural elements (doors/windows)")
                # Note: In a full implementation, we would filter lines that intersect with
                # these elements. For now, we just log them.
                # TODO: Implement line filtering based on Rekognition bounding boxes
        
        if not filtered_lines:
            raise HTTPException(
                status_code=400, 
                detail="No lines remaining after filtering. Try adjusting filter parameters."
            )
        
        # Convert to wall segments
        print("🏗️  Converting to wall segments...")
        wall_segments_dict = line_filter.convert_to_wall_segments(
            filtered_lines,
            image_width=image_width,
            image_height=image_height
        )
        
        # Convert to WallSegment objects for validation
        wall_segments = [
            ParserWallSegment(
                start=(seg['start'][0], seg['start'][1]),
                end=(seg['end'][0], seg['end'][1]),
                is_load_bearing=seg.get('is_load_bearing', False)
            )
            for seg in wall_segments_dict
        ]
        
        # Validate segments (with relaxed connectivity check for images)
        print("✅ Validating segments...")
        # For image-extracted segments, use non-strict mode and allow higher isolated ratio
        # since endpoints may need snapping tolerance applied
        validation_result = validate_image_segments(wall_segments, strict=False)
        
        if not validation_result['valid']:
            warnings = validation_result.get('warnings', [])
            errors = validation_result.get('errors', [])
            if errors:
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation failed: {'; '.join(errors)}"
                )
            if warnings:
                print(f"⚠️  Validation warnings: {'; '.join(warnings)}")
        
        # Detect rooms using existing algorithm
        print("🔍 Detecting rooms...")
        # Convert wall segments to temporary JSON for detect_rooms function
        import json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            walls_data = [
                {
                    "type": "line",
                    "start": [seg.start[0], seg.start[1]],
                    "end": [seg.end[0], seg.end[1]],
                    "is_load_bearing": seg.is_load_bearing
                }
                for seg in wall_segments
            ]
            json.dump(walls_data, f)
            temp_json_path = f.name
        
        try:
            # Use higher tolerance for image-extracted segments (matching validator)
            # Image coordinates may have precision issues after normalization
            rooms = detect_rooms(temp_json_path, tolerance=5.0)
            print(f"✅ Detected {len(rooms)} rooms")
        finally:
            if os.path.exists(temp_json_path):
                os.unlink(temp_json_path)
        
        # Convert to PRD-compliant format (remove confidence, ensure array format)
        prd_compliant_rooms = []
        for room in rooms:
            prd_compliant_rooms.append({
                "id": room["id"],
                "bounding_box": room["bounding_box"],
                "name_hint": room.get("name_hint", "")
            })
        
        return prd_compliant_rooms
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    finally:
        # Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@app.post("/detect-rooms", response_model=List[Dict[str, Any]])
async def detect_rooms_endpoint(request: RoomDetectionRequest):
    """
    Detect rooms from wall line segments.
    
    Accepts a list of wall segments and returns detected rooms with bounding boxes.
    Returns a JSON array of rooms per PRD specification.
    
    Each room contains:
    - id: Unique identifier (e.g., "room_001")
    - bounding_box: Normalized coordinates [x_min, y_min, x_max, y_max] (0-1000 range)
    - name_hint: Optional name hint (e.g., "Room 1")
    """
    import json
    import tempfile
    
    try:
        # Convert request to temporary JSON file for processing
        walls_data = [wall.model_dump() for wall in request.walls]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(walls_data, f)
            temp_path = f.name
        
        try:
            # Detect rooms - returns list of rooms with id, bounding_box, name_hint
            rooms = detect_rooms(temp_path, tolerance=1.0)
            
            # Remove confidence field to match PRD (only id, bounding_box, name_hint)
            # PRD doesn't specify confidence in the output format
            prd_compliant_rooms = []
            for room in rooms:
                prd_compliant_rooms.append({
                    "id": room["id"],
                    "bounding_box": room["bounding_box"],
                    "name_hint": room["name_hint"]
                })
            
            return prd_compliant_rooms
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error detecting rooms: {str(e)}")


@app.get("/test/simple")
async def test_simple():
    """Test endpoint with simple floorplan. Returns PRD-compliant array format."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "tests", "sample_data", "simple", "simple_floorplan.json")
    rooms = detect_rooms(json_path, tolerance=1.0)
    # Return PRD-compliant format (array of rooms)
    prd_compliant_rooms = []
    for room in rooms:
        prd_compliant_rooms.append({
            "id": room["id"],
            "bounding_box": room["bounding_box"],
            "name_hint": room["name_hint"]
        })
    return prd_compliant_rooms


@app.get("/test/complex")
async def test_complex():
    """Test endpoint with complex floorplan. Returns PRD-compliant array format."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "tests", "sample_data", "complex", "complex_floorplan.json")
    rooms = detect_rooms(json_path, tolerance=1.0)
    # Return PRD-compliant format (array of rooms)
    prd_compliant_rooms = []
    for room in rooms:
        prd_compliant_rooms.append({
            "id": room["id"],
            "bounding_box": room["bounding_box"],
            "name_hint": room["name_hint"]
        })
    return prd_compliant_rooms


@app.post("/graph-data", response_model=Dict[str, Any])
async def get_graph_data(request: RoomDetectionRequest):
    """
    Get wall adjacency graph data for visualization.
    
    Returns nodes, edges, and detected cycles/faces for graph visualization.
    """
    from src.room_detector import build_wall_graph, find_faces_using_polygonize, find_faces_in_planar_graph, filter_cycles
    from src.parser import parse_line_segments
    from src.graph_serializer import graph_to_json
    import tempfile
    import json
    
    try:
        # Convert request to temporary JSON file for processing
        walls_data = [wall.model_dump() for wall in request.walls]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(walls_data, f)
            temp_path = f.name
        
        try:
            # Parse segments
            segments = parse_line_segments(temp_path)
            
            # Build graph
            graph = build_wall_graph(segments, tolerance=1.0)
            
            # Find faces (same logic as detect_rooms)
            faces = find_faces_using_polygonize(segments)
            if not faces:
                faces = find_faces_in_planar_graph(graph)
            
            # Filter valid faces
            valid_faces = filter_cycles(faces, min_area=100.0, min_perimeter=40.0)
            
            # Serialize graph to JSON
            graph_data = graph_to_json(graph, valid_faces)
            
            return graph_data
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating graph data: {str(e)}")
