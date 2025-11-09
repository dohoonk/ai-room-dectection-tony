"""
Amazon Rekognition integration for object detection.

Detects architectural elements (doors, windows, furniture) and filters
non-wall lines from blueprints.
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict, List, Any
import os
from datetime import datetime


class RekognitionClient:
    """Client for interacting with Amazon Rekognition."""
    
    def __init__(self,
                 region_name: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        """
        Initialize Rekognition client.
        
        Args:
            region_name: AWS region (defaults to AWS_REGION env var or 'us-east-1')
            aws_access_key_id: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret key (defaults to AWS_SECRET_ACCESS_KEY env var)
        """
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        
        try:
            self.rekognition_client = boto3.client(
                'rekognition',
                region_name=self.region_name,
                aws_access_key_id=aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Rekognition client: {str(e)}")
    
    def detect_labels(self,
                     s3_bucket: str,
                     s3_object_key: str,
                     max_labels: int = 100,
                     min_confidence: float = 50.0) -> Dict[str, Any]:
        """
        Detect labels (objects, scenes) in an image stored in S3.
        
        Args:
            s3_bucket: S3 bucket name
            s3_object_key: S3 object key (file path)
            max_labels: Maximum number of labels to return
            min_confidence: Minimum confidence threshold (0-100)
            
        Returns:
            Dictionary containing:
            - Labels: List of detected labels with confidence scores
            - LabelCount: Total number of labels detected
            - ImageProperties: Image metadata (dimensions, etc.)
            - ArchitecturalElements: Filtered list of relevant architectural elements
            
        Raises:
            ClientError: If Rekognition API call fails
        """
        try:
            response = self.rekognition_client.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_object_key
                    }
                },
                MaxLabels=max_labels,
                MinConfidence=min_confidence
            )
            
            labels = response.get('Labels', [])
            
            # Filter for architectural elements
            architectural_elements = self._filter_architectural_elements(labels)
            
            return {
                'labels': labels,
                'label_count': response.get('LabelCount', 0),
                'image_properties': response.get('ImageProperties', {}),
                'architectural_elements': architectural_elements,
                'response_metadata': response.get('ResponseMetadata', {})
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': f"Rekognition error: {error_message}"}},
                operation_name='DetectLabels'
            )
    
    def detect_text(self,
                   s3_bucket: str,
                   s3_object_key: str) -> Dict[str, Any]:
        """
        Detect text in an image (OCR) using Rekognition.
        
        Note: For better OCR results, use Textract instead.
        This is useful for simple text detection in images.
        
        Args:
            s3_bucket: S3 bucket name
            s3_object_key: S3 object key (file path)
            
        Returns:
            Dictionary containing:
            - TextDetections: List of detected text with bounding boxes
            - Text: Concatenated text content
            
        Raises:
            ClientError: If Rekognition API call fails
        """
        try:
            response = self.rekognition_client.detect_text(
                Image={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_object_key
                    }
                }
            )
            
            text_detections = response.get('TextDetections', [])
            
            # Extract text lines (filter out words, keep only lines)
            lines = [det for det in text_detections if det.get('Type') == 'LINE']
            words = [det for det in text_detections if det.get('Type') == 'WORD']
            
            # Concatenate text
            full_text = ' '.join([det['DetectedText'] for det in lines])
            
            return {
                'text_detections': text_detections,
                'lines': lines,
                'words': words,
                'text': full_text,
                'response_metadata': response.get('ResponseMetadata', {})
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': f"Rekognition error: {error_message}"}},
                operation_name='DetectText'
            )
    
    def _filter_architectural_elements(self, labels: List[Dict]) -> List[Dict[str, Any]]:
        """
        Filter labels for architectural elements relevant to room detection.
        
        Args:
            labels: List of Rekognition labels
            
        Returns:
            List of filtered architectural elements
        """
        # Keywords for architectural elements
        architectural_keywords = [
            'door', 'window', 'furniture', 'appliance', 'fixture',
            'cabinet', 'sink', 'toilet', 'bathtub', 'shower',
            'stove', 'refrigerator', 'oven', 'microwave', 'dishwasher',
            'bed', 'table', 'chair', 'sofa', 'desk'
        ]
        
        architectural_elements = []
        
        for label in labels:
            label_name = label.get('Name', '').lower()
            confidence = label.get('Confidence', 0)
            
            # Check if label matches architectural keywords
            matches = any(keyword in label_name for keyword in architectural_keywords)
            
            if matches:
                architectural_elements.append({
                    'name': label.get('Name', ''),
                    'confidence': confidence,
                    'categories': [cat.get('Name', '') for cat in label.get('Categories', [])],
                    'instances': label.get('Instances', [])  # Bounding boxes if available
                })
        
        return architectural_elements
    
    def filter_non_wall_lines(self,
                              s3_bucket: str,
                              s3_object_key: str,
                              lines: List[Dict]) -> List[Dict]:
        """
        Filter out lines that are likely non-wall elements based on Rekognition detection.
        
        This helps remove lines that represent doors, windows, furniture, etc.
        
        Args:
            s3_bucket: S3 bucket name
            s3_object_key: S3 object key (file path)
            lines: List of line segments to filter (with geometry/bounding boxes)
            
        Returns:
            Filtered list of lines (walls only, non-architectural elements removed)
        """
        try:
            # Detect architectural elements
            result = self.detect_labels(s3_bucket, s3_object_key, min_confidence=60.0)
            architectural_elements = result['architectural_elements']
            
            if not architectural_elements:
                # No architectural elements detected, return all lines
                return lines
            
            # Get bounding boxes of detected elements
            element_boxes = []
            for element in architectural_elements:
                instances = element.get('instances', [])
                for instance in instances:
                    bbox = instance.get('BoundingBox', {})
                    if bbox:
                        element_boxes.append(bbox)
            
            # Filter lines that intersect with architectural element bounding boxes
            filtered_lines = []
            for line in lines:
                line_bbox = line.get('geometry', {}).get('BoundingBox', {})
                if not line_bbox:
                    # No bounding box, keep the line
                    filtered_lines.append(line)
                    continue
                
                # Check if line intersects with any architectural element
                intersects = False
                for elem_bbox in element_boxes:
                    if self._bounding_boxes_intersect(line_bbox, elem_bbox):
                        intersects = True
                        break
                
                # Keep line if it doesn't intersect with architectural elements
                if not intersects:
                    filtered_lines.append(line)
            
            return filtered_lines
            
        except Exception as e:
            # If Rekognition fails, return all lines (fail-safe)
            print(f"Warning: Rekognition filtering failed: {e}. Returning all lines.")
            return lines
    
    def _bounding_boxes_intersect(self, bbox1: Dict, bbox2: Dict) -> bool:
        """
        Check if two bounding boxes intersect.
        
        Args:
            bbox1: First bounding box (with Left, Top, Width, Height)
            bbox2: Second bounding box (with Left, Top, Width, Height)
            
        Returns:
            True if boxes intersect, False otherwise
        """
        left1 = bbox1.get('Left', 0.0)
        top1 = bbox1.get('Top', 0.0)
        width1 = bbox1.get('Width', 0.0)
        height1 = bbox1.get('Height', 0.0)
        
        left2 = bbox2.get('Left', 0.0)
        top2 = bbox2.get('Top', 0.0)
        width2 = bbox2.get('Width', 0.0)
        height2 = bbox2.get('Height', 0.0)
        
        right1 = left1 + width1
        bottom1 = top1 + height1
        right2 = left2 + width2
        bottom2 = top2 + height2
        
        # Check for intersection
        return not (right1 < left2 or right2 < left1 or bottom1 < top2 or bottom2 < top1)


def create_rekognition_client(region_name: Optional[str] = None) -> RekognitionClient:
    """
    Convenience function to create Rekognition client with default configuration.
    
    Args:
        region_name: Optional region name override
        
    Returns:
        RekognitionClient instance
    """
    return RekognitionClient(region_name=region_name)

