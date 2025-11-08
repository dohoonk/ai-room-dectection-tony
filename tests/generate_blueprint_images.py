"""Script to generate blueprint images from JSON wall data."""
import json
from PIL import Image, ImageDraw
import os

def generate_blueprint_image(json_path, output_path, width=1000, height=1000):
    """Generate a blueprint image from JSON wall data."""
    # Read JSON file
    with open(json_path, 'r') as f:
        walls = json.load(f)
    
    # Create image with white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw grid lines for reference (light gray)
    grid_spacing = 100
    for x in range(0, width, grid_spacing):
        draw.line([(x, 0), (x, height)], fill='lightgray', width=1)
    for y in range(0, height, grid_spacing):
        draw.line([(0, y), (width, y)], fill='lightgray', width=1)
    
    # Draw walls
    for wall in walls:
        start = tuple(wall['start'])
        end = tuple(wall['end'])
        is_load_bearing = wall.get('is_load_bearing', False)
        
        # Use thicker, darker lines for load-bearing walls
        line_width = 4 if is_load_bearing else 2
        line_color = 'black' if is_load_bearing else 'darkgray'
        
        draw.line([start, end], fill=line_color, width=line_width)
        
        # Draw small circles at endpoints
        draw.ellipse([start[0]-3, start[1]-3, start[0]+3, start[1]+3], fill='red')
        draw.ellipse([end[0]-3, end[1]-3, end[0]+3, end[1]+3], fill='red')
    
    # Save image
    img.save(output_path)
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    # Generate simple floorplan image
    simple_json = 'sample_data/simple/simple_floorplan.json'
    simple_image = 'sample_data/simple/simple_floorplan.png'
    if os.path.exists(simple_json):
        generate_blueprint_image(simple_json, simple_image)
    
    # Generate complex floorplan image
    complex_json = 'sample_data/complex/complex_floorplan.json'
    complex_image = 'sample_data/complex/complex_floorplan.png'
    if os.path.exists(complex_json):
        generate_blueprint_image(complex_json, complex_image)

