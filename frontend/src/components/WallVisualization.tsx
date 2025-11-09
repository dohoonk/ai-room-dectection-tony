import React, { useRef, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { Room } from '../services/api';

interface WallSegment {
  type: string;
  start: [number, number];
  end: [number, number];
  is_load_bearing?: boolean;
}

interface WallVisualizationProps {
  walls: WallSegment[] | null;
  rooms?: Room[];
  selectedRoomId?: string | null;
  onRoomClick?: (roomId: string) => void;
}

const WallVisualization: React.FC<WallVisualizationProps> = ({ 
  walls, 
  rooms = [], 
  selectedRoomId = null,
  onRoomClick 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = React.useState({ width: 800, height: 600 });

  useEffect(() => {
    // Calculate canvas dimensions based on wall coordinates or room bounding boxes
    if (!walls || walls.length === 0) {
      // If no walls, use room bounding boxes to determine canvas size
      if (rooms && rooms.length > 0) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        rooms.forEach(room => {
          const [x1, y1, x2, y2] = room.bounding_box;
          minX = Math.min(minX, x1, x2);
          minY = Math.min(minY, y1, y2);
          maxX = Math.max(maxX, x1, x2);
          maxY = Math.max(maxY, y1, y2);
        });
        const padding = 50;
        const width = maxX - minX + padding * 2;
        const height = maxY - minY + padding * 2;
        setDimensions({ width: Math.max(800, width), height: Math.max(600, height) });
      }
      return;
    }

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

    walls.forEach(wall => {
      const [x1, y1] = wall.start;
      const [x2, y2] = wall.end;
      minX = Math.min(minX, x1, x2);
      minY = Math.min(minY, y1, y2);
      maxX = Math.max(maxX, x1, x2);
      maxY = Math.max(maxY, y1, y2);
    });

    // Add padding
    const padding = 50;
    const width = maxX - minX + padding * 2;
    const height = maxY - minY + padding * 2;

    setDimensions({ width: Math.max(800, width), height: Math.max(600, height) });
  }, [walls]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !walls || walls.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      // Canvas context not available (e.g., in test environment)
      return;
    }

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Set canvas size
    canvas.width = dimensions.width;
    canvas.height = dimensions.height;

    // Calculate bounds for scaling
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    walls.forEach(wall => {
      const [x1, y1] = wall.start;
      const [x2, y2] = wall.end;
      minX = Math.min(minX, x1, x2);
      minY = Math.min(minY, y1, y2);
      maxX = Math.max(maxX, x1, x2);
      maxY = Math.max(maxY, y1, y2);
    });

    const padding = 50;
    const scaleX = (canvas.width - padding * 2) / (maxX - minX || 1);
    const scaleY = (canvas.height - padding * 2) / (maxY - minY || 1);
    const scale = Math.min(scaleX, scaleY);

    // Draw grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 0.5;
    const gridSize = 50;
    for (let x = 0; x < canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Draw walls (if available)
    if (walls && walls.length > 0) {
      walls.forEach(wall => {
      const [x1, y1] = wall.start;
      const [x2, y2] = wall.end;

      // Transform coordinates
      const startX = padding + (x1 - minX) * scale;
      const startY = padding + (y1 - minY) * scale;
      const endX = padding + (x2 - minX) * scale;
      const endY = padding + (y2 - minY) * scale;

      // Draw wall line
      ctx.strokeStyle = wall.is_load_bearing ? '#d32f2f' : '#1976d2';
      ctx.lineWidth = wall.is_load_bearing ? 3 : 2;
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.stroke();

      // Draw endpoints
      ctx.fillStyle = '#1976d2';
      ctx.beginPath();
      ctx.arc(startX, startY, 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(endX, endY, 4, 0, 2 * Math.PI);
      ctx.fill();
      });
    }

    // Draw room bounding boxes
    if (rooms.length > 0) {
      rooms.forEach(room => {
        const [roomMinX, roomMinY, roomMaxX, roomMaxY] = room.bounding_box;
        const isSelected = selectedRoomId === room.id;

        // Transform bounding box coordinates
        const boxMinX = padding + (roomMinX - minX) * scale;
        const boxMinY = padding + (roomMinY - minY) * scale;
        const boxMaxX = padding + (roomMaxX - minX) * scale;
        const boxMaxY = padding + (roomMaxY - minY) * scale;

        const boxWidth = boxMaxX - boxMinX;
        const boxHeight = boxMaxY - boxMinY;

        // Draw bounding box
        ctx.strokeStyle = isSelected ? '#ff9800' : '#4caf50';
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.setLineDash(isSelected ? [] : [5, 5]);
        ctx.strokeRect(boxMinX, boxMinY, boxWidth, boxHeight);
        ctx.setLineDash([]);

        // Fill with semi-transparent color
        ctx.fillStyle = isSelected ? 'rgba(255, 152, 0, 0.2)' : 'rgba(76, 175, 80, 0.1)';
        ctx.fillRect(boxMinX, boxMinY, boxWidth, boxHeight);

        // Draw room name label (use name_hint if available, otherwise use id)
        const roomLabel = room.name_hint || room.id;
        ctx.fillStyle = isSelected ? '#ff9800' : '#4caf50';
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        const labelX = boxMinX + 5;
        const labelY = boxMinY + 5;
        
        // Draw background for text
        const textMetrics = ctx.measureText(roomLabel);
        const textWidth = textMetrics.width;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.fillRect(labelX - 2, labelY - 2, textWidth + 4, 18);
        
        // Draw text
        ctx.fillStyle = isSelected ? '#ff9800' : '#4caf50';
        ctx.fillText(roomLabel, labelX, labelY);
      });
    }
  }, [walls, dimensions, rooms, selectedRoomId, onRoomClick]);

  // Handle canvas clicks for room selection
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onRoomClick || rooms.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Calculate bounds for scaling
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    
    if (walls && walls.length > 0) {
      walls.forEach(wall => {
        const [x1, y1] = wall.start;
        const [x2, y2] = wall.end;
        minX = Math.min(minX, x1, x2);
        minY = Math.min(minY, y1, y2);
        maxX = Math.max(maxX, x1, x2);
        maxY = Math.max(maxY, y1, y2);
      });
    } else if (rooms && rooms.length > 0) {
      // Use room bounding boxes if no walls
      rooms.forEach(room => {
        const [x1, y1, x2, y2] = room.bounding_box;
        minX = Math.min(minX, x1, x2);
        minY = Math.min(minY, y1, y2);
        maxX = Math.max(maxX, x1, x2);
        maxY = Math.max(maxY, y1, y2);
      });
    } else {
      return; // No data
    }

    const padding = 50;
    const scaleX = (canvas.width - padding * 2) / (maxX - minX || 1);
    const scaleY = (canvas.height - padding * 2) / (maxY - minY || 1);
    const scale = Math.min(scaleX, scaleY);

    // Convert click coordinates back to original coordinate system
    const originalX = (x - padding) / scale + minX;
    const originalY = (y - padding) / scale + minY;

    // Check if click is inside any room bounding box
    for (const room of rooms) {
      const [boxMinX, boxMinY, boxMaxX, boxMaxY] = room.bounding_box;
      if (
        originalX >= boxMinX &&
        originalX <= boxMaxX &&
        originalY >= boxMinY &&
        originalY <= boxMaxY
      ) {
        onRoomClick(room.id);
        break;
      }
    }
  };

  if ((!walls || walls.length === 0) && (!rooms || rooms.length === 0)) {
    return (
      <Typography variant="body2" color="text.secondary">
        No data to visualize
      </Typography>
    );
  }

  return (
    <Box ref={containerRef} sx={{ overflow: 'auto', border: '1px solid #e0e0e0', borderRadius: 1 }}>
      <canvas
        ref={canvasRef}
        onClick={handleCanvasClick}
        style={{
          display: 'block',
          maxWidth: '100%',
          cursor: rooms.length > 0 ? 'pointer' : 'default',
        }}
      />
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1, px: 1 }}>
        {walls && walls.length > 0 && `Walls: ${walls.length} | `}Blue: Regular walls | Red: Load-bearing walls
        {rooms.length > 0 && ` | Green: Rooms (${rooms.length} detected) | Click to select`}
      </Typography>
    </Box>
  );
};

export default WallVisualization;

