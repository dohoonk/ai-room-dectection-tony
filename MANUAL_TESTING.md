# Manual Testing Guide

## Backend API Testing

### 1. Start the Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the run script:
```bash
cd backend
chmod +x run.sh
./run.sh
```

The server will start at: `http://localhost:8000`

### 2. Test Health Endpoints

**Root endpoint:**
```bash
curl http://localhost:8000/
```

**Health check:**
```bash
curl http://localhost:8000/health
```

### 3. Test Room Detection Endpoint

**Using curl with a test file:**

```bash
curl -X POST http://localhost:8000/detect-rooms \
  -H "Content-Type: application/json" \
  -d @../tests/sample_data/test_floorplan.json
```

**Using curl with inline JSON:**

```bash
curl -X POST http://localhost:8000/detect-rooms \
  -H "Content-Type: application/json" \
  -d '{
    "walls": [
      {"type": "line", "start": [100, 100], "end": [400, 100], "is_load_bearing": false},
      {"type": "line", "start": [400, 100], "end": [400, 300], "is_load_bearing": false},
      {"type": "line", "start": [400, 300], "end": [100, 300], "is_load_bearing": false},
      {"type": "line", "start": [100, 300], "end": [100, 100], "is_load_bearing": false}
    ]
  }'
```

### 4. Test Pre-configured Endpoints

**Simple floorplan:**
```bash
curl http://localhost:8000/test/simple
```

**Complex floorplan:**
```bash
curl http://localhost:8000/test/complex
```

### 5. Using Postman

1. **Create a new POST request:**
   - URL: `http://localhost:8000/detect-rooms`
   - Method: POST
   - Headers: `Content-Type: application/json`

2. **Body (raw JSON):**
```json
{
  "walls": [
    {"type": "line", "start": [100, 100], "end": [400, 100], "is_load_bearing": false},
    {"type": "line", "start": [400, 100], "end": [400, 300], "is_load_bearing": false},
    {"type": "line", "start": [400, 300], "end": [100, 300], "is_load_bearing": false},
    {"type": "line", "start": [100, 300], "end": [100, 100], "is_load_bearing": false}
  ]
}
```

3. **Send the request** and check the response

### 6. Test with Different Floorplans

**L-shaped floorplan:**
```bash
curl -X POST http://localhost:8000/detect-rooms \
  -H "Content-Type: application/json" \
  -d @../tests/sample_data/test_l_shape_floorplan.json
```

**Multi-room floorplan:**
```bash
curl -X POST http://localhost:8000/detect-rooms \
  -H "Content-Type: application/json" \
  -d @../tests/sample_data/test_multiroom_floorplan.json
```

### 7. Test Error Handling

**Invalid JSON (missing fields):**
```bash
curl -X POST http://localhost:8000/detect-rooms \
  -H "Content-Type: application/json" \
  -d '{
    "walls": [
      {"type": "line", "start": [100, 100]}
    ]
  }'
```

**Empty walls array:**
```bash
curl -X POST http://localhost:8000/detect-rooms \
  -H "Content-Type: application/json" \
  -d '{"walls": []}'
```

## Frontend Testing (After Task 11)

Once the frontend is integrated:

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm start`
3. Open browser: `http://localhost:3000`
4. Upload a JSON file using the FileUpload component
5. View detected rooms on the canvas

## Expected Response Format

Successful response:
```json
[
  {
    "id": "room_001",
    "bounding_box": [100.0, 100.0, 400.0, 300.0],
    "name_hint": "Room"
  }
]
```

Error response:
```json
{
  "detail": "Error detecting rooms: <error message>"
}
```

