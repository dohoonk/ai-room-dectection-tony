import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUpload from '../FileUpload';

// Mock FileReader
class MockFileReader {
  result: string | null = null;
  onload: ((e: ProgressEvent<FileReader>) => void) | null = null;
  onerror: ((e: ProgressEvent<FileReader>) => void) | null = null;

  readAsText(file: File) {
    // Simulate async read
    setTimeout(() => {
      if (this.onload) {
        const event = {
          target: { result: this.result },
        } as ProgressEvent<FileReader>;
        this.onload(event);
      }
    }, 0);
  }
}

describe('FileUpload', () => {
  const mockOnFileUpload = jest.fn();
  let originalFileReader: typeof FileReader;

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock FileReader
    originalFileReader = global.FileReader;
    (global as any).FileReader = jest.fn(() => new MockFileReader());
  });

  afterEach(() => {
    global.FileReader = originalFileReader;
  });

  it('renders upload button', () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} />);
    expect(screen.getByText('Upload JSON File')).toBeInTheDocument();
  });

  it('handles file selection', async () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} />);
    
    const file = new File(
      [JSON.stringify([{ type: 'line', start: [0, 0], end: [100, 100] }])],
      'test.json',
      { type: 'application/json' }
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();

    // Mock FileReader with proper async handling
    const mockReader = new MockFileReader();
    const jsonData = JSON.stringify([{ type: 'line', start: [0, 0], end: [100, 100] }]);
    mockReader.result = jsonData;
    
    (global.FileReader as jest.Mock).mockImplementation(() => {
      const reader = new MockFileReader();
      reader.result = jsonData;
      // Trigger onload immediately
      setTimeout(() => {
        if (reader.onload) {
          const event = {
            target: { result: jsonData },
          } as ProgressEvent<FileReader>;
          reader.onload(event);
        }
      }, 10);
      return reader;
    });

    // Simulate file selection
    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
    });

    const event = new Event('change', { bubbles: true });
    input.dispatchEvent(event);
    
    await waitFor(() => {
      expect(mockOnFileUpload).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            type: 'line',
            start: [0, 0],
            end: [100, 100],
          }),
        ])
      );
    }, { timeout: 3000 });
  });

  it('shows error for non-JSON files', async () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} />);
    
    const file = new File(['not json'], 'test.txt', { type: 'text/plain' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (input) {
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });

      const event = new Event('change', { bubbles: true });
      input.dispatchEvent(event);
      
      await waitFor(() => {
        expect(screen.getByText(/please upload a json file/i)).toBeInTheDocument();
      }, { timeout: 2000 });
      expect(mockOnFileUpload).not.toHaveBeenCalled();
    }
  });

  it('shows error for invalid JSON', async () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} />);
    
    const file = new File(['{ invalid json }'], 'test.json', { type: 'application/json' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (input) {
      const mockReader = new MockFileReader();
      mockReader.result = '{ invalid json }';
      (global.FileReader as jest.Mock).mockImplementation(() => mockReader);

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });

      const event = new Event('change', { bubbles: true });
      input.dispatchEvent(event);
      
      await waitFor(() => {
        expect(screen.getByText(/error parsing json/i)).toBeInTheDocument();
      }, { timeout: 2000 });
      expect(mockOnFileUpload).not.toHaveBeenCalled();
    }
  });

  it('shows error for non-array JSON', async () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} />);
    
    const file = new File(
      [JSON.stringify({ not: 'an array' })],
      'test.json',
      { type: 'application/json' }
    );
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (input) {
      const mockReader = new MockFileReader();
      mockReader.result = JSON.stringify({ not: 'an array' });
      (global.FileReader as jest.Mock).mockImplementation(() => mockReader);

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });

      const event = new Event('change', { bubbles: true });
      input.dispatchEvent(event);
      
      await waitFor(() => {
        expect(screen.getByText(/json must contain an array/i)).toBeInTheDocument();
      }, { timeout: 2000 });
      expect(mockOnFileUpload).not.toHaveBeenCalled();
    }
  });

  it('shows error for invalid wall segment structure', async () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} />);
    
    const file = new File(
      [JSON.stringify([{ type: 'line' }])], // Missing start and end
      'test.json',
      { type: 'application/json' }
    );
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (input) {
      const mockReader = new MockFileReader();
      mockReader.result = JSON.stringify([{ type: 'line' }]);
      (global.FileReader as jest.Mock).mockImplementation(() => mockReader);

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });

      const event = new Event('change', { bubbles: true });
      input.dispatchEvent(event);
      
      await waitFor(() => {
        expect(screen.getByText(/invalid wall segment structure/i)).toBeInTheDocument();
      }, { timeout: 2000 });
      expect(mockOnFileUpload).not.toHaveBeenCalled();
    }
  });
});
