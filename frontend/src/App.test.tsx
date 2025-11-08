import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import { detectRooms, Room } from './services/api';

// Mock the API service
jest.mock('./services/api');
const mockDetectRooms = detectRooms as jest.MockedFunction<typeof detectRooms>;

// Mock FileReader to work synchronously in tests
const originalFileReader = global.FileReader;
class MockFileReader {
  result: string | null = null;
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  readAsText(file: File) {
    // Simulate reading file content synchronously
    file.text().then((text) => {
      this.result = text;
      if (this.onload) {
        const event = {
          target: { result: this.result },
        } as ProgressEvent<FileReader>;
        this.onload.call(this as any, event);
      }
    }).catch(() => {
      if (this.onerror) {
        this.onerror.call(this as any, {} as ProgressEvent<FileReader>);
      }
    });
  }
}

// Override FileReader for tests
(global as any).FileReader = MockFileReader;

describe('App Component', () => {
  beforeEach(() => {
    mockDetectRooms.mockClear();
  });

  test('renders Room Detection AI title', () => {
    render(<App />);
    const titleElement = screen.getByText(/Room Detection AI/i);
    expect(titleElement).toBeInTheDocument();
  });

  test('renders file upload component', () => {
    render(<App />);
    const uploadButton = screen.getByText(/Upload JSON File/i);
    expect(uploadButton).toBeInTheDocument();
  });

  test('renders description text', () => {
    render(<App />);
    const description = screen.getByText(/Upload a JSON file containing wall line segments/i);
    expect(description).toBeInTheDocument();
  });

  test('displays loading state when detecting rooms', async () => {
    mockDetectRooms.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve([]), 200))
    );

    render(<App />);
    
    // Create a mock file
    const file = new File(['[{"type":"line","start":[0,0],"end":[100,0]}]'], 'test.json', {
      type: 'application/json',
    });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Create a proper FileList mock
    const fileList = {
      0: file,
      length: 1,
      item: (index: number) => (index === 0 ? file : null),
      [Symbol.iterator]: function* () {
        yield file;
      },
    } as FileList;

    Object.defineProperty(input, 'files', {
      value: fileList,
      writable: false,
    });

    // Simulate file change event
    const event = new Event('change', { bubbles: true });
    input.dispatchEvent(event);

    // Wait for FileReader to process and API call to start
    await waitFor(() => {
      expect(screen.getByText(/Detecting rooms/i)).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  test('displays error message when API call fails', async () => {
    mockDetectRooms.mockRejectedValueOnce(new Error('API Error'));

    render(<App />);

    const file = new File(['[{"type":"line","start":[0,0],"end":[100,0]}]'], 'test.json', {
      type: 'application/json',
    });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    const fileList = {
      0: file,
      length: 1,
      item: (index: number) => (index === 0 ? file : null),
      [Symbol.iterator]: function* () {
        yield file;
      },
    } as FileList;

    Object.defineProperty(input, 'files', {
      value: fileList,
      writable: false,
    });

    const event = new Event('change', { bubbles: true });
    input.dispatchEvent(event);

    await new Promise(resolve => setTimeout(resolve, 10));

    await waitFor(() => {
      expect(screen.getByText(/API Error/i)).toBeInTheDocument();
    });
  });

  test('displays room count when rooms are detected', async () => {
    const mockRooms: Room[] = [
      { id: 'room_001', bounding_box: [0, 0, 100, 100] as [number, number, number, number], name_hint: 'Room' },
      { id: 'room_002', bounding_box: [100, 0, 200, 100] as [number, number, number, number], name_hint: 'Room' },
    ];
    mockDetectRooms.mockResolvedValueOnce(mockRooms);

    render(<App />);

    const file = new File(['[{"type":"line","start":[0,0],"end":[100,0]}]'], 'test.json', {
      type: 'application/json',
    });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    const fileList = {
      0: file,
      length: 1,
      item: (index: number) => (index === 0 ? file : null),
      [Symbol.iterator]: function* () {
        yield file;
      },
    } as FileList;

    Object.defineProperty(input, 'files', {
      value: fileList,
      writable: false,
    });

    const event = new Event('change', { bubbles: true });
    input.dispatchEvent(event);

    await new Promise(resolve => setTimeout(resolve, 10));

    await waitFor(() => {
      expect(screen.getByText(/2 rooms detected/i)).toBeInTheDocument();
    });
  });

  test('calls detectRooms API when file is uploaded', async () => {
    mockDetectRooms.mockResolvedValueOnce([]);

    render(<App />);

    const file = new File(['[{"type":"line","start":[0,0],"end":[100,0]}]'], 'test.json', {
      type: 'application/json',
    });

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    const fileList = {
      0: file,
      length: 1,
      item: (index: number) => (index === 0 ? file : null),
      [Symbol.iterator]: function* () {
        yield file;
      },
    } as FileList;

    Object.defineProperty(input, 'files', {
      value: fileList,
      writable: false,
    });

    const event = new Event('change', { bubbles: true });
    input.dispatchEvent(event);

    await new Promise(resolve => setTimeout(resolve, 10));

    await waitFor(() => {
      expect(mockDetectRooms).toHaveBeenCalled();
    });
  });
});
