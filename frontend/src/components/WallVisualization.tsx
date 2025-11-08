import React, { useRef, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

interface WallSegment {
  type: string;
  start: [number, number];
  end: [number, number];
  is_load_bearing?: boolean;
}

interface WallVisualizationProps {
  walls: WallSegment[];
}

const WallVisualization: React.FC<WallVisualizationProps> = ({ walls }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = React.useState({ width: 800, height: 600 });

  useEffect(() => {
    // Calculate canvas dimensions based on wall coordinates
    if (walls.length === 0) return;

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
    if (!canvas || walls.length === 0) return;

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

    // Draw walls
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
  }, [walls, dimensions]);

  if (walls.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No wall data to visualize
      </Typography>
    );
  }

  return (
    <Box ref={containerRef} sx={{ overflow: 'auto', border: '1px solid #e0e0e0', borderRadius: 1 }}>
      <canvas
        ref={canvasRef}
        style={{
          display: 'block',
          maxWidth: '100%',
        }}
      />
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1, px: 1 }}>
        Walls: {walls.length} | Blue: Regular walls | Red: Load-bearing walls
      </Typography>
    </Box>
  );
};

export default WallVisualization;

