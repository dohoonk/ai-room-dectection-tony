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
import { detectRooms, WallSegment, Room } from './services/api';
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

  const handleFileUpload = async (data: WallSegment[]) => {
    setWallData(data);
    setRooms(null);
    setSelectedRoomId(null);
    setError(null);
    setLoading(true);

    try {
      const detectedRooms = await detectRooms(data);
      setRooms(detectedRooms);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect rooms');
    } finally {
      setLoading(false);
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
