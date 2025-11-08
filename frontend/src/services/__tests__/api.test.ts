/**
 * Tests for API service
 */
import { detectRooms, checkHealth, WallSegment, Room, RoomDetectionResponse } from '../api';

// Mock fetch
global.fetch = jest.fn();

describe('API Service', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  describe('detectRooms', () => {
    const mockWalls: WallSegment[] = [
      { type: 'line', start: [0, 0], end: [100, 0], is_load_bearing: false },
      { type: 'line', start: [100, 0], end: [100, 100], is_load_bearing: false },
      { type: 'line', start: [100, 100], end: [0, 100], is_load_bearing: false },
      { type: 'line', start: [0, 100], end: [0, 0], is_load_bearing: false },
    ];

    it('should successfully detect rooms', async () => {
      const mockResponse: RoomDetectionResponse = {
        rooms: [
          {
            id: 'room_001',
            bounding_box: [0, 0, 100, 100] as [number, number, number, number],
            name_hint: 'Room',
          },
        ],
        metrics: {
          processing_time: 0.5,
          confidence_score: 0.85,
          rooms_count: 1
        }
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await detectRooms(mockWalls);
      expect(result).toEqual(mockResponse);
      expect(result.rooms).toHaveLength(1);
      expect(result.metrics).toBeDefined();
      expect(result.metrics.processing_time).toBe(0.5);
      expect(result.metrics.confidence_score).toBe(0.85);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/detect-rooms',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });

    it('should handle API errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid input' }),
      });

      await expect(detectRooms(mockWalls)).rejects.toThrow('Invalid input');
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(detectRooms(mockWalls)).rejects.toThrow('Network error');
    });

    it('should handle unknown errors', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({}),
      });

      await expect(detectRooms(mockWalls)).rejects.toThrow();
    });
  });

  describe('checkHealth', () => {
    it('should return health status', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      const result = await checkHealth();
      expect(result).toEqual({ status: 'healthy' });
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/health');
    });

    it('should handle health check failures', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(checkHealth()).rejects.toThrow('Backend server is not available');
    });

    it('should handle network errors', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(checkHealth()).rejects.toThrow('Backend server is not available');
    });
  });
});

