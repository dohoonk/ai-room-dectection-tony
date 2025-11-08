import React from 'react';
import { render, screen } from '@testing-library/react';
import WallVisualization from '../WallVisualization';

describe('WallVisualization', () => {
  const mockWalls = [
    { type: 'line', start: [0, 0], end: [100, 0], is_load_bearing: false },
    { type: 'line', start: [100, 0], end: [100, 100], is_load_bearing: false },
    { type: 'line', start: [100, 100], end: [0, 100], is_load_bearing: false },
    { type: 'line', start: [0, 100], end: [0, 0], is_load_bearing: false },
  ];

  it('renders canvas element', () => {
    render(<WallVisualization walls={mockWalls} />);
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('displays message when no walls provided', () => {
    render(<WallVisualization walls={[]} />);
    expect(screen.getByText(/no wall data to visualize/i)).toBeInTheDocument();
  });

  it('displays wall count and legend', () => {
    render(<WallVisualization walls={mockWalls} />);
    expect(screen.getByText(/walls: 4/i)).toBeInTheDocument();
    expect(screen.getByText(/blue: regular walls/i)).toBeInTheDocument();
  });

  it('handles walls with load bearing property', () => {
    const wallsWithLoadBearing = [
      { type: 'line', start: [0, 0], end: [100, 0], is_load_bearing: true },
      { type: 'line', start: [100, 0], end: [100, 100], is_load_bearing: false },
    ];
    render(<WallVisualization walls={wallsWithLoadBearing} />);
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('handles walls without load bearing property', () => {
    const wallsWithoutLoadBearing = [
      { type: 'line', start: [0, 0], end: [100, 0] },
      { type: 'line', start: [100, 0], end: [100, 100] },
    ];
    render(<WallVisualization walls={wallsWithoutLoadBearing} />);
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });
});

