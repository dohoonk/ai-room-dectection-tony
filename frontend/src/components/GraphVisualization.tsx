import React, { useRef, useEffect, useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import FitScreenIcon from '@mui/icons-material/FitScreen';
import Tooltip from '@mui/material/Tooltip';
import { styled } from '@mui/material/styles';

interface GraphNode {
  id: number;
  x: number;
  y: number;
  label: string;
}

interface GraphEdge {
  id: string;
  source: number;
  target: number;
  sourceCoords: [number, number];
  targetCoords: [number, number];
  isLoadBearing: boolean;
}

interface GraphCycle {
  id: string;
  nodes: number[];
  coords: [number, number][];
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  cycles: GraphCycle[];
  stats: {
    nodeCount: number;
    edgeCount: number;
    cycleCount: number;
  };
}

interface GraphVisualizationProps {
  graphData: GraphData | null;
  width?: number;
  height?: number;
}

const VisualizationContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
  overflow: 'hidden',
  backgroundColor: theme.palette.background.paper,
}));

const ControlsContainer = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: theme.spacing(1),
  right: theme.spacing(1),
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(0.5),
  zIndex: 10,
  backgroundColor: 'rgba(255, 255, 255, 0.9)',
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(0.5),
}));

const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  graphData,
  width = 800,
  height = 600,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Calculate bounds for auto-fit
  const calculateBounds = useCallback(() => {
    if (!graphData || graphData.nodes.length === 0) {
      return { minX: 0, minY: 0, maxX: width, maxY: height };
    }

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    
    graphData.nodes.forEach(node => {
      minX = Math.min(minX, node.x);
      minY = Math.min(minY, node.y);
      maxX = Math.max(maxX, node.x);
      maxY = Math.max(maxY, node.y);
    });

    // Add padding
    const padding = 50;
    return {
      minX: minX - padding,
      minY: minY - padding,
      maxX: maxX + padding,
      maxY: maxY + padding,
    };
  }, [graphData, width, height]);

  // Auto-fit to bounds
  const fitToBounds = useCallback(() => {
    const bounds = calculateBounds();
    const graphWidth = bounds.maxX - bounds.minX;
    const graphHeight = bounds.maxY - bounds.minY;
    
    if (graphWidth === 0 || graphHeight === 0) return;

    const scaleX = width / graphWidth;
    const scaleY = height / graphHeight;
    const newZoom = Math.min(scaleX, scaleY) * 0.9; // 90% to add padding

    const centerX = (bounds.minX + bounds.maxX) / 2;
    const centerY = (bounds.minY + bounds.maxY) / 2;

    setZoom(newZoom);
    setPan({
      x: width / 2 - centerX * newZoom,
      y: height / 2 - centerY * newZoom,
    });
  }, [calculateBounds, width, height]);

  // Auto-fit on data load
  useEffect(() => {
    if (graphData && graphData.nodes.length > 0) {
      fitToBounds();
    }
  }, [graphData, fitToBounds]);

  // Zoom controls
  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 5));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.2, 0.1));
  };

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (e.button === 0) { // Left mouse button
      setIsDragging(true);
      setDragStart({
        x: e.clientX - pan.x,
        y: e.clientY - pan.y,
      });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Transform coordinates
  const transformX = (x: number) => x * zoom + pan.x;
  const transformY = (y: number) => y * zoom + pan.y;

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <Paper sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No graph data available. Upload a floorplan to visualize the wall adjacency graph.
        </Typography>
      </Paper>
    );
  }

  return (
    <VisualizationContainer sx={{ width, height }}>
      <ControlsContainer>
        <Tooltip title="Zoom In">
          <IconButton size="small" onClick={handleZoomIn}>
            <ZoomInIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out">
          <IconButton size="small" onClick={handleZoomOut}>
            <ZoomOutIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Fit to Screen">
          <IconButton size="small" onClick={fitToBounds}>
            <FitScreenIcon />
          </IconButton>
        </Tooltip>
      </ControlsContainer>

      <Box sx={{ position: 'absolute', top: 8, left: 8, zIndex: 10 }}>
        <Paper sx={{ p: 1, backgroundColor: 'rgba(255, 255, 255, 0.9)' }}>
          <Typography variant="caption" display="block">
            Nodes: {graphData.stats.nodeCount}
          </Typography>
          <Typography variant="caption" display="block">
            Edges: {graphData.stats.edgeCount}
          </Typography>
          <Typography variant="caption" display="block">
            Cycles: {graphData.stats.cycleCount}
          </Typography>
        </Paper>
      </Box>

      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          {/* Arrow marker for directed edges (if needed) */}
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#666" />
          </marker>
        </defs>

        {/* Draw cycles first (behind edges) */}
        {graphData.cycles.map((cycle, cycleIdx) => {
          if (cycle.coords.length < 3) return null;
          
          const cyclePath = cycle.coords
            .map((coord, idx) => {
              const x = transformX(coord[0]);
              const y = transformY(coord[1]);
              return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
            })
            .join(' ') + ' Z';

          return (
            <path
              key={cycle.id}
              d={cyclePath}
              fill={`hsl(${(cycleIdx * 60) % 360}, 70%, 90%)`}
              stroke={`hsl(${(cycleIdx * 60) % 360}, 70%, 50%)`}
              strokeWidth={2}
              strokeDasharray="5,5"
              opacity={0.6}
            />
          );
        })}

        {/* Draw edges */}
        {graphData.edges.map(edge => {
          const x1 = transformX(edge.sourceCoords[0]);
          const y1 = transformY(edge.sourceCoords[1]);
          const x2 = transformX(edge.targetCoords[0]);
          const y2 = transformY(edge.targetCoords[1]);

          return (
            <line
              key={edge.id}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={edge.isLoadBearing ? '#d32f2f' : '#666'}
              strokeWidth={edge.isLoadBearing ? 2.5 : 1.5}
              opacity={0.7}
            />
          );
        })}

        {/* Draw nodes */}
        {graphData.nodes.map(node => {
          const x = transformX(node.x);
          const y = transformY(node.y);
          const nodeRadius = 4 * zoom;

          return (
            <g key={node.id}>
              <circle
                cx={x}
                cy={y}
                r={nodeRadius}
                fill="#1976d2"
                stroke="#fff"
                strokeWidth={1}
              />
              {/* Show label on hover (optional) */}
            </g>
          );
        })}
      </svg>
    </VisualizationContainer>
  );
};

export default GraphVisualization;

