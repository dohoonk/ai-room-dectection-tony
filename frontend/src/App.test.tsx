import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

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
