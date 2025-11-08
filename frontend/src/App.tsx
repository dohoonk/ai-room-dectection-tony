import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import FileUpload from './components/FileUpload';
import WallVisualization from './components/WallVisualization';
import MetricsDisplay from './components/MetricsDisplay';
import { detectRooms, WallSegment, Room, DetectionMetrics } from './services/api';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [wallData, setWallData] = React.useState<WallSegment[] | null>(null);
  const [rooms, setRooms] = React.useState<Room[] | null>(null);
  const [selectedRoomId, setSelectedRoomId] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [metrics, setMetrics] = React.useState<DetectionMetrics | null>(null);
  const [processingStartTime, setProcessingStartTime] = React.useState<number | null>(null);

  const handleFileUpload = async (data: WallSegment[]) => {
    setWallData(data);
    setRooms(null);
    setSelectedRoomId(null);
    setError(null);
    setMetrics(null);
    setLoading(true);
    
    // Track processing start time for client-side measurement
    const startTime = performance.now();
    setProcessingStartTime(startTime);

    try {
      const response = await detectRooms(data);
      setRooms(response.rooms);
      
      // Use backend metrics if available, otherwise calculate client-side
      if (response.metrics) {
        setMetrics(response.metrics);
      } else {
        const clientProcessingTime = (performance.now() - startTime) / 1000;
        setMetrics({
          processing_time: clientProcessingTime,
          confidence_score: 0.0,
          rooms_count: response.rooms.length
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect rooms');
    } finally {
      setLoading(false);
      setProcessingStartTime(null);
    }
  };

  const handleRoomClick = (roomId: string) => {
    setSelectedRoomId(selectedRoomId === roomId ? null : roomId);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Room Detection AI
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Upload a JSON file containing wall line segments to visualize the floorplan.
          </Typography>
          
          <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
            <FileUpload onFileUpload={handleFileUpload} />
          </Paper>

          {loading && (
            <Paper elevation={3} sx={{ p: 3, mt: 3, textAlign: 'center' }}>
              <CircularProgress />
              <Typography variant="body2" sx={{ mt: 2 }}>
                Detecting rooms...
              </Typography>
            </Paper>
          )}

          {error && (
            <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
              <Alert severity="error">{error}</Alert>
            </Paper>
          )}

          {metrics && (
            <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
              <MetricsDisplay
                roomsCount={metrics.rooms_count}
                processingTime={metrics.processing_time}
                confidenceScore={metrics.confidence_score}
              />
            </Paper>
          )}

          {wallData && (
            <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Floorplan Visualization
              </Typography>
              {rooms && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {rooms.length} room{rooms.length !== 1 ? 's' : ''} detected
                </Typography>
              )}
              <WallVisualization 
                walls={wallData} 
                rooms={rooms || []}
                selectedRoomId={selectedRoomId}
                onRoomClick={handleRoomClick}
              />
            </Paper>
          )}
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
