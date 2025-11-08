# Room Detection AI

Automatic detection of room boundaries in architectural floorplans using graph-based algorithms.

## Project Structure

```
.
├── frontend/          # React + Material UI frontend
├── backend/           # Python FastAPI backend
├── tests/             # Test data and utilities
└── .taskmaster/       # Task management files
```

## Development Setup

### Prerequisites
- Node.js v22.20.0+
- Python 3.12.2+
- npm 10.9.3+

### Frontend Setup
```bash
cd frontend
npm install
npm start          # Start development server
npm test           # Run tests
```

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest              # Run tests
```

## Tech Stack

### Frontend
- React (TypeScript)
- Material UI
- Jest + React Testing Library

### Backend
- FastAPI
- NetworkX (graph algorithms)
- Shapely (geometry processing)
- Pytest

## Getting Started

See `.taskmaster/tasks/` for detailed task breakdowns.

