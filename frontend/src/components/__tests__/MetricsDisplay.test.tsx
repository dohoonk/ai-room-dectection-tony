import React from 'react';
import { render, screen } from '@testing-library/react';
import MetricsDisplay from '../MetricsDisplay';

describe('MetricsDisplay Component', () => {
  test('renders metrics display with all values', () => {
    render(
      <MetricsDisplay
        roomsCount={3}
        processingTime={1.234}
        confidenceScore={0.85}
      />
    );

    expect(screen.getByText('Detection Metrics')).toBeInTheDocument();
    expect(screen.getByText('Rooms Detected')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Processing Time')).toBeInTheDocument();
    expect(screen.getByText('1.23 seconds')).toBeInTheDocument();
    expect(screen.getByText('Confidence Score')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  test('displays N/A for missing processing time', () => {
    render(
      <MetricsDisplay
        roomsCount={2}
        confidenceScore={0.75}
      />
    );

    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  test('displays N/A for missing confidence score', () => {
    render(
      <MetricsDisplay
        roomsCount={1}
        processingTime={0.5}
      />
    );

    const confidenceElements = screen.getAllByText('N/A');
    expect(confidenceElements.length).toBeGreaterThan(0);
  });

  test('formats processing time in milliseconds for values less than 1 second', () => {
    render(
      <MetricsDisplay
        roomsCount={1}
        processingTime={0.456}
        confidenceScore={0.9}
      />
    );

    expect(screen.getByText('456 ms')).toBeInTheDocument();
  });

  test('formats processing time in seconds for values >= 1 second', () => {
    render(
      <MetricsDisplay
        roomsCount={2}
        processingTime={2.567}
        confidenceScore={0.8}
      />
    );

    expect(screen.getByText('2.57 seconds')).toBeInTheDocument();
  });

  test('displays high confidence score in success color (>= 0.8)', () => {
    const { container } = render(
      <MetricsDisplay
        roomsCount={1}
        processingTime={1.0}
        confidenceScore={0.9}
      />
    );

    const confidenceElement = screen.getByText('90%');
    expect(confidenceElement).toHaveStyle({ color: expect.stringContaining('success') });
  });

  test('displays medium confidence score in warning color (0.6-0.8)', () => {
    const { container } = render(
      <MetricsDisplay
        roomsCount={1}
        processingTime={1.0}
        confidenceScore={0.7}
      />
    );

    const confidenceElement = screen.getByText('70%');
    expect(confidenceElement).toHaveStyle({ color: expect.stringContaining('warning') });
  });

  test('displays low confidence score in error color (< 0.6)', () => {
    const { container } = render(
      <MetricsDisplay
        roomsCount={1}
        processingTime={1.0}
        confidenceScore={0.5}
      />
    );

    const confidenceElement = screen.getByText('50%');
    expect(confidenceElement).toHaveStyle({ color: expect.stringContaining('error') });
  });

  test('handles zero rooms count', () => {
    render(
      <MetricsDisplay
        roomsCount={0}
        processingTime={0.1}
        confidenceScore={0.0}
      />
    );

    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  test('renders all three metric sections', () => {
    render(
      <MetricsDisplay
        roomsCount={5}
        processingTime={3.141}
        confidenceScore={0.92}
      />
    );

    expect(screen.getByText('Rooms Detected')).toBeInTheDocument();
    expect(screen.getByText('Processing Time')).toBeInTheDocument();
    expect(screen.getByText('Confidence Score')).toBeInTheDocument();
  });
});

