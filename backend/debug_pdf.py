"""
Debug script to analyze PDF structure and understand why lines aren't being extracted.

This script will:
1. Open the PDF and examine its structure
2. Check for vector graphics (drawings)
3. Check for raster images
4. Analyze drawing properties
5. Try different extraction methods
"""

import fitz  # PyMuPDF
import sys
import os
from typing import Dict, Any, List


def analyze_pdf_structure(pdf_path: str):
    """Comprehensive analysis of PDF structure."""
    print("=" * 70)
    print(f"📄 Analyzing PDF: {os.path.basename(pdf_path)}")
    print("=" * 70)
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"❌ Error opening PDF: {e}")
        return
    
    print(f"\n📊 PDF Metadata:")
    print(f"   Pages: {len(doc)}")
    print(f"   Is PDF: {doc.is_pdf}")
    print(f"   Needs password: {doc.needs_pass}")
    
    # Analyze each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"\n{'=' * 70}")
        print(f"📄 Page {page_num + 1}")
        print(f"{'=' * 70}")
        
        # Page dimensions
        rect = page.rect
        print(f"\n📐 Page Dimensions:")
        print(f"   Width: {rect.width:.2f} points")
        print(f"   Height: {rect.height:.2f} points")
        print(f"   Bounding box: {rect}")
        
        # Check for drawings (vector graphics)
        print(f"\n🎨 Vector Graphics (Drawings):")
        drawings = page.get_drawings()
        print(f"   Total drawings: {len(drawings)}")
        
        if drawings:
            print(f"\n   Drawing Details:")
            for i, drawing in enumerate(drawings[:10]):  # Show first 10
                print(f"\n   Drawing {i + 1}:")
                print(f"     Keys: {list(drawing.keys())}")
                
                # Check width/thickness
                width = drawing.get("width")
                print(f"     Width/Thickness: {width} (type: {type(width).__name__})")
                
                # Check color
                color = drawing.get("color")
                print(f"     Color: {color} (type: {type(color).__name__})")
                
                # Check items (path commands)
                items = drawing.get("items", [])
                print(f"     Items (path commands): {len(items)}")
                
                if items:
                    # Count by type
                    item_types = {}
                    for item in items[:5]:  # Show first 5 items
                        if item and len(item) > 0:
                            cmd = item[0]
                            item_types[cmd] = item_types.get(cmd, 0) + 1
                            print(f"       Item: {item}")
                    
                    print(f"     Item type counts: {item_types}")
        else:
            print("   ⚠️  No drawings found on this page")
        
        # Check for text
        print(f"\n📝 Text Content:")
        text = page.get_text()
        if text.strip():
            print(f"   Text found: {len(text)} characters")
            print(f"   Preview: {text[:200]}...")
        else:
            print("   No text found")
        
        # Check for images
        print(f"\n🖼️  Images:")
        image_list = page.get_images()
        print(f"   Total images: {len(image_list)}")
        if image_list:
            for i, img in enumerate(image_list[:5]):  # Show first 5
                print(f"   Image {i + 1}: xref={img[0]}, smask={img[1]}, width={img[2]}, height={img[3]}")
        
        # Check for text blocks (OCR-like)
        print(f"\n📋 Text Blocks:")
        blocks = page.get_text("blocks")
        print(f"   Total text blocks: {len(blocks)}")
        if blocks:
            print(f"   First block: {blocks[0]}")
        
        # Try alternative extraction methods
        print(f"\n🔍 Alternative Extraction Methods:")
        
        # Method 1: get_displaylist
        try:
            display_list = page.get_displaylist()
            print(f"   DisplayList items: {len(display_list)}")
        except Exception as e:
            print(f"   DisplayList error: {e}")
        
        # Method 2: get_text("dict") for structured text
        try:
            text_dict = page.get_text("dict")
            print(f"   Text dict blocks: {len(text_dict.get('blocks', []))}")
        except Exception as e:
            print(f"   Text dict error: {e}")
        
        # Method 3: Check for paths
        try:
            paths = page.get_paths()
            print(f"   Paths found: {len(paths)}")
            if paths:
                for i, path in enumerate(paths[:3]):
                    print(f"     Path {i + 1}: {path}")
        except Exception as e:
            print(f"   Paths error: {e}")
    
    doc.close()
    
    print(f"\n{'=' * 70}")
    print("✅ Analysis complete")
    print(f"{'=' * 70}")


def try_extraction_methods(pdf_path: str):
    """Try different extraction methods to find lines."""
    print(f"\n{'=' * 70}")
    print("🔬 Trying Different Extraction Methods")
    print(f"{'=' * 70}")
    
    doc = fitz.open(pdf_path)
    
    for page_num in range(min(1, len(doc))):  # Just first page for testing
        page = doc[page_num]
        print(f"\n📄 Page {page_num + 1}:")
        
        # Method 1: Our current method (get_drawings)
        print("\n1️⃣  Method: get_drawings()")
        drawings = page.get_drawings()
        print(f"   Found {len(drawings)} drawings")
        
        line_count = 0
        for drawing in drawings:
            items = drawing.get("items", [])
            for item in items:
                if item and len(item) > 0 and item[0] == "l":  # Line command
                    line_count += 1
        print(f"   Lines found: {line_count}")
        
        # Method 2: Check all items in all drawings
        print("\n2️⃣  Method: All drawing items")
        all_items = []
        for drawing in drawings:
            items = drawing.get("items", [])
            all_items.extend(items)
        
        item_types = {}
        for item in all_items:
            if item and len(item) > 0:
                cmd = item[0]
                item_types[cmd] = item_types.get(cmd, 0) + 1
        
        print(f"   Item types: {item_types}")
        print(f"   Total items: {len(all_items)}")
        
        # Method 3: Check for rects
        print("\n3️⃣  Method: get_rects()")
        try:
            rects = page.get_rects()
            print(f"   Rects found: {len(rects)}")
            if rects:
                print(f"   First rect: {rects[0]}")
        except Exception as e:
            print(f"   Error: {e}")
    
    doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_pdf.py <path_to_pdf>")
        print("\nExample:")
        print("  python debug_pdf.py ../House-Floor-Plans.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Run analysis
    analyze_pdf_structure(pdf_path)
    
    # Try extraction methods
    try_extraction_methods(pdf_path)

