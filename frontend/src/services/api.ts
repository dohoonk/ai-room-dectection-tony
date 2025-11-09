/**
 * API service for room detection
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface WallSegment {
  type: string;
  start: [number, number];
  end: [number, number];
  is_load_bearing?: boolean;
}

export interface Room {
  id: string;
  bounding_box: [number, number, number, number]; // [min_x, min_y, max_x, max_y]
  name_hint: string;
  confidence?: number; // 0.00 to 1.00
}

export interface DetectionMetrics {
  processing_time: number; // in seconds
  confidence_score: number; // 0.00 to 1.00
  rooms_count: number;
}

// PRD-compliant response: array of rooms directly
export type RoomDetectionResponse = Room[];

export interface GraphNode {
  id: number;
  x: number;
  y: number;
  label: string;
}

export interface GraphEdge {
  id: string;
  source: number;
  target: number;
  sourceCoords: [number, number];
  targetCoords: [number, number];
  isLoadBearing: boolean;
}

export interface GraphCycle {
  id: string;
  nodes: number[];
  coords: [number, number][];
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  cycles: GraphCycle[];
  stats: {
    nodeCount: number;
    edgeCount: number;
    cycleCount: number;
  };
}

export interface RoomDetectionRequest {
  walls: WallSegment[];
}

/**
 * Get graph data for visualization
 */
export async function getGraphData(walls: WallSegment[]): Promise<GraphData> {
  try {
    const response = await fetch(`${API_BASE_URL}/graph-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ walls }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: GraphData = await response.json();
    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Network error: Failed to connect to the API');
  }
}

/**
 * Detect rooms from wall segments
 */
export async function detectRooms(walls: WallSegment[]): Promise<RoomDetectionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/detect-rooms`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ walls }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: RoomDetectionResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Network error: Failed to connect to the API');
  }
}

/**
 * Detect rooms from PDF file
 */
export async function detectRoomsFromPdf(
  file: File,
  useTextract: boolean = false,
  useRekognition: boolean = false
): Promise<RoomDetectionResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams();
    if (useTextract) params.append('use_textract', 'true');
    if (useRekognition) params.append('use_rekognition', 'true');

    const url = `${API_BASE_URL}/detect-rooms-from-pdf${params.toString() ? '?' + params.toString() : ''}`;
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: RoomDetectionResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Network error: Failed to connect to the API');
  }
}

/**
 * Detect rooms from image file (PNG, JPG, JPEG, etc.)
 */
export async function detectRoomsFromImage(
  file: File,
  useTextract: boolean = false,
  useRekognition: boolean = false,
  parameters?: any  // ImageProcessingParameters from ParameterTuning component
): Promise<RoomDetectionResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('use_textract', useTextract.toString());
    formData.append('use_rekognition', useRekognition.toString());
    
    // Add parameters as JSON string if provided
    if (parameters) {
      formData.append('parameters', JSON.stringify(parameters));
    }

    const response = await fetch(`${API_BASE_URL}/detect-rooms-from-image`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: RoomDetectionResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Network error: Failed to connect to the API');
  }
}

/**
 * Health check endpoint
 */
export async function checkHealth(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    throw new Error('Backend server is not available');
  }
}

