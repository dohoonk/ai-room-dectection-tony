"""
Amazon Textract integration for OCR and text extraction.

Extracts text labels, dimensions, and other text content from PDF and image files
stored in S3.
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict, List, Any
import os
import json
from datetime import datetime


class TextractClient:
    """Client for interacting with Amazon Textract."""
    
    def __init__(self,
                 region_name: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        """
        Initialize Textract client.
        
        Args:
            region_name: AWS region (defaults to AWS_REGION env var or 'us-east-1')
            aws_access_key_id: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret key (defaults to AWS_SECRET_ACCESS_KEY env var)
        """
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        
        try:
            self.textract_client = boto3.client(
                'textract',
                region_name=self.region_name,
                aws_access_key_id=aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Textract client: {str(e)}")
    
    def detect_document_text(self, 
                            s3_bucket: str,
                            s3_object_key: str) -> Dict[str, Any]:
        """
        Detect text in a document stored in S3.
        
        This is the basic OCR operation that extracts all text from a document.
        
        Args:
            s3_bucket: S3 bucket name
            s3_object_key: S3 object key (file path)
            
        Returns:
            Dictionary containing:
            - Blocks: List of detected text blocks
            - Text: Concatenated text content
            - Lines: List of detected lines
            - Words: List of detected words
            - DocumentMetadata: Metadata about the document
            
        Raises:
            ClientError: If Textract API call fails
        """
        try:
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_object_key
                    }
                }
            )
            
            # Extract and organize text content
            blocks = response.get('Blocks', [])
            text_lines = []
            words = []
            
            for block in blocks:
                if block['BlockType'] == 'LINE':
                    text_lines.append({
                        'text': block.get('Text', ''),
                        'confidence': block.get('Confidence', 0),
                        'geometry': block.get('Geometry', {})
                    })
                elif block['BlockType'] == 'WORD':
                    words.append({
                        'text': block.get('Text', ''),
                        'confidence': block.get('Confidence', 0),
                        'geometry': block.get('Geometry', {})
                    })
            
            # Concatenate all text
            full_text = ' '.join([line['text'] for line in text_lines])
            
            return {
                'blocks': blocks,
                'text': full_text,
                'lines': text_lines,
                'words': words,
                'document_metadata': response.get('DocumentMetadata', {}),
                'response_metadata': response.get('ResponseMetadata', {})
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': f"Textract error: {error_message}"}},
                operation_name='DetectDocumentText'
            )
    
    def analyze_document(self,
                        s3_bucket: str,
                        s3_object_key: str,
                        feature_types: List[str] = ['FORMS', 'TABLES']) -> Dict[str, Any]:
        """
        Analyze document structure (forms, tables, key-value pairs).
        
        More advanced than detect_document_text - extracts structured data.
        
        Args:
            s3_bucket: S3 bucket name
            s3_object_key: S3 object key (file path)
            feature_types: List of features to detect ['FORMS', 'TABLES', 'SIGNATURES']
            
        Returns:
            Dictionary containing:
            - Blocks: List of detected blocks
            - DocumentMetadata: Metadata about the document
            - Forms: Extracted form fields (key-value pairs)
            - Tables: Extracted table data
            
        Raises:
            ClientError: If Textract API call fails
        """
        try:
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_object_key
                    }
                },
                FeatureTypes=feature_types
            )
            
            blocks = response.get('Blocks', [])
            
            # Extract forms (key-value pairs)
            forms = self._extract_forms(blocks)
            
            # Extract tables
            tables = self._extract_tables(blocks)
            
            return {
                'blocks': blocks,
                'forms': forms,
                'tables': tables,
                'document_metadata': response.get('DocumentMetadata', {}),
                'response_metadata': response.get('ResponseMetadata', {})
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': f"Textract error: {error_message}"}},
                operation_name='AnalyzeDocument'
            )
    
    def _extract_forms(self, blocks: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract key-value pairs (forms) from blocks.
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            List of form fields with keys and values
        """
        forms = []
        key_blocks = {}
        value_blocks = {}
        
        # Separate key and value blocks
        for block in blocks:
            if block['BlockType'] == 'KEY_VALUE_SET':
                entity_types = block.get('EntityTypes', [])
                block_id = block['Id']
                
                if 'KEY' in entity_types:
                    key_blocks[block_id] = block
                elif 'VALUE' in entity_types:
                    value_blocks[block_id] = block
        
        # Match keys with values
        for key_id, key_block in key_blocks.items():
            relationships = key_block.get('Relationships', [])
            for relationship in relationships:
                if relationship['Type'] == 'VALUE':
                    value_ids = relationship.get('Ids', [])
                    for value_id in value_ids:
                        if value_id in value_blocks:
                            value_block = value_blocks[value_id]
                            forms.append({
                                'key': self._get_text_from_block(key_block, blocks),
                                'value': self._get_text_from_block(value_block, blocks),
                                'key_confidence': key_block.get('Confidence', 0),
                                'value_confidence': value_block.get('Confidence', 0)
                            })
        
        return forms
    
    def _extract_tables(self, blocks: List[Dict]) -> List[List[List[str]]]:
        """
        Extract table data from blocks.
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            List of tables, each table is a list of rows, each row is a list of cells
        """
        tables = []
        table_blocks = [b for b in blocks if b['BlockType'] == 'TABLE']
        
        for table_block in table_blocks:
            # Get cells in this table
            relationships = table_block.get('Relationships', [])
            cell_ids = []
            for relationship in relationships:
                if relationship['Type'] == 'CHILD':
                    cell_ids.extend(relationship.get('Ids', []))
            
            # Organize cells by row and column
            cells = {}
            for cell_id in cell_ids:
                cell_block = next((b for b in blocks if b['Id'] == cell_id), None)
                if cell_block and cell_block['BlockType'] == 'CELL':
                    row_index = cell_block.get('RowIndex', 0)
                    col_index = cell_block.get('ColumnIndex', 0)
                    if row_index not in cells:
                        cells[row_index] = {}
                    cells[row_index][col_index] = self._get_text_from_block(cell_block, blocks)
            
            # Convert to list of lists
            if cells:
                max_row = max(cells.keys())
                max_col = max(max(row.keys()) for row in cells.values())
                table = []
                for row_idx in range(1, max_row + 1):
                    row = []
                    for col_idx in range(1, max_col + 1):
                        row.append(cells.get(row_idx, {}).get(col_idx, ''))
                    table.append(row)
                tables.append(table)
        
        return tables
    
    def _get_text_from_block(self, block: Dict, all_blocks: List[Dict]) -> str:
        """
        Extract text from a block by following relationships to word blocks.
        
        Args:
            block: The block to extract text from
            all_blocks: All blocks from the response
            
        Returns:
            Concatenated text from the block
        """
        text_parts = []
        relationships = block.get('Relationships', [])
        
        for relationship in relationships:
            if relationship['Type'] == 'CHILD':
                child_ids = relationship.get('Ids', [])
                for child_id in child_ids:
                    child_block = next((b for b in all_blocks if b['Id'] == child_id), None)
                    if child_block and child_block['BlockType'] == 'WORD':
                        text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts)
    
    def extract_room_labels(self,
                           s3_bucket: str,
                           s3_object_key: str) -> List[Dict[str, Any]]:
        """
        Extract room labels and dimensions from a blueprint.
        
        This is a specialized function that looks for common room label patterns
        and dimension text in architectural blueprints.
        
        Args:
            s3_bucket: S3 bucket name
            s3_object_key: S3 object key (file path)
            
        Returns:
            List of detected room labels with their text and positions
        """
        # Use basic text detection first
        result = self.detect_document_text(s3_bucket, s3_object_key)
        
        room_labels = []
        
        # Common room label patterns
        room_keywords = [
            'kitchen', 'bedroom', 'bathroom', 'living room', 'dining room',
            'office', 'study', 'garage', 'basement', 'attic', 'hallway',
            'closet', 'pantry', 'laundry', 'utility', 'storage', 'room'
        ]
        
        # Extract lines that might be room labels
        for line in result['lines']:
            text_lower = line['text'].lower()
            
            # Check if line contains room keywords or looks like a label
            is_room_label = any(keyword in text_lower for keyword in room_keywords)
            
            # Also check for patterns like "Room 1", "R-101", etc.
            import re
            if re.match(r'^(room|r-?)\s*\d+', text_lower, re.IGNORECASE):
                is_room_label = True
            
            if is_room_label:
                room_labels.append({
                    'text': line['text'],
                    'confidence': line['confidence'],
                    'geometry': line['geometry']
                })
        
        return room_labels


def create_textract_client(region_name: Optional[str] = None) -> TextractClient:
    """
    Convenience function to create Textract client with default configuration.
    
    Args:
        region_name: Optional region name override
        
    Returns:
        TextractClient instance
    """
    return TextractClient(region_name=region_name)

