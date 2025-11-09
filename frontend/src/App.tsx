import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import ViewInArIcon from '@mui/icons-material/ViewInAr';
import CodeIcon from '@mui/icons-material/Code';
import SettingsIcon from '@mui/icons-material/Settings';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import FileUpload from './components/FileUpload';
import WallVisualization from './components/WallVisualization';
import MetricsDisplay from './components/MetricsDisplay';
import GraphVisualization from './components/GraphVisualization';
import ParameterTuning, { ImageProcessingParameters, DEFAULT_PARAMETERS, STORAGE_KEY } from './components/ParameterTuning';
import { detectRooms, detectRoomsFromPdf, detectRoomsFromImage, getGraphData, WallSegment, Room, DetectionMetrics, GraphData } from './services/api';
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
  const [renamingRoomId, setRenamingRoomId] = React.useState<string | null>(null);
  const [renameDialogOpen, setRenameDialogOpen] = React.useState(false);
  const [newRoomName, setNewRoomName] = React.useState('');
  const [graphData, setGraphData] = React.useState<GraphData | null>(null);
  const [showGraphView, setShowGraphView] = React.useState(false);
  const [showJsonView, setShowJsonView] = React.useState(false);
  const [parameterTuningOpen, setParameterTuningOpen] = React.useState(false);
  const [imageProcessingParams, setImageProcessingParams] = React.useState<ImageProcessingParameters>(DEFAULT_PARAMETERS);

  // Load saved parameters from localStorage on mount
  React.useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setImageProcessingParams({ ...DEFAULT_PARAMETERS, ...parsed });
      } catch (e) {
        console.warn('Failed to parse saved parameters:', e);
      }
    }
  }, []);

  const handleFileUpload = async (data: WallSegment[]) => {
    setWallData(data);
    setRooms(null);
    setSelectedRoomId(null);
    setError(null);
    setMetrics(null);
    setGraphData(null);
    setLoading(true);
    
    // Track processing start time for client-side measurement
    const startTime = performance.now();
    setProcessingStartTime(startTime);

    try {
      // Fetch both room detection and graph data in parallel
      const [roomsArray, graphResponse] = await Promise.all([
        detectRooms(data),
        getGraphData(data).catch((err) => {
          // Log error but don't fail the whole operation
          console.warn('Failed to fetch graph data:', err);
          return null;
        })
      ]);
      
      // PRD-compliant response is now just an array of rooms
      setRooms(roomsArray);
      setGraphData(graphResponse);
      
      // Log graph data status for debugging
      if (graphResponse) {
        console.log('Graph data loaded:', graphResponse.stats);
      } else {
        console.warn('Graph data is null - graph view will be disabled');
      }
      
      // Calculate metrics client-side (PRD doesn't include metrics in API response)
      const clientProcessingTime = (performance.now() - startTime) / 1000;
      // Calculate average confidence from rooms (if we had it, but PRD doesn't include it)
      // For now, we'll use a default or calculate based on room count
      const estimatedConfidence = roomsArray.length > 0 ? 1.0 : 0.0;
      
      setMetrics({
        processing_time: clientProcessingTime,
        confidence_score: estimatedConfidence,
        rooms_count: roomsArray.length
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect rooms');
    } finally {
      setLoading(false);
      setProcessingStartTime(null);
    }
  };

  const handleImageUpload = async (file: File) => {
    setWallData(null); // Images don't have raw wall data for visualization
    setRooms(null);
    setSelectedRoomId(null);
    setError(null);
    setMetrics(null);
    setGraphData(null);
    setLoading(true);
    
    // Track processing start time for client-side measurement
    const startTime = performance.now();
    setProcessingStartTime(startTime);

    try {
      // Call image detection API with current processing parameters
      const roomsArray = await detectRoomsFromImage(file, false, false, imageProcessingParams);
      
      // PRD-compliant response is now just an array of rooms
      setRooms(roomsArray);
      
      // Calculate metrics client-side
      const clientProcessingTime = (performance.now() - startTime) / 1000;
      const estimatedConfidence = roomsArray.length > 0 ? 1.0 : 0.0;
      
      setMetrics({
        processing_time: clientProcessingTime,
        confidence_score: estimatedConfidence,
        rooms_count: roomsArray.length,
      });
      
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      setRooms(null);
      setMetrics(null);
    } finally {
      setLoading(false);
      setProcessingStartTime(null);
    }
  };

  const handlePdfUpload = async (file: File) => {
    setWallData(null); // PDF doesn't provide wall data directly
    setRooms(null);
    setSelectedRoomId(null);
    setError(null);
    setMetrics(null);
    setGraphData(null);
    setLoading(true);
    
    // Track processing start time
    const startTime = performance.now();
    setProcessingStartTime(startTime);

    try {
      // Call PDF endpoint (without AWS services for now - can add toggle later)
      const roomsArray = await detectRoomsFromPdf(file, false, false);
      
      setRooms(roomsArray);
      
      // Graph data not available for PDF uploads (would need to extract segments first)
      setGraphData(null);
      
      // Calculate metrics client-side
      const clientProcessingTime = (performance.now() - startTime) / 1000;
      const estimatedConfidence = roomsArray.length > 0 ? 1.0 : 0.0;
      
      setMetrics({
        processing_time: clientProcessingTime,
        confidence_score: estimatedConfidence,
        rooms_count: roomsArray.length
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process PDF');
    } finally {
      setLoading(false);
      setProcessingStartTime(null);
    }
  };

  const handleRoomClick = (roomId: string) => {
    setSelectedRoomId(selectedRoomId === roomId ? null : roomId);
  };

  const handleRenameRoom = (roomId: string) => {
    const room = rooms?.find(r => r.id === roomId);
    if (room) {
      setRenamingRoomId(roomId);
      setNewRoomName(room.name_hint || room.id);
      setRenameDialogOpen(true);
    }
  };

  const handleRenameConfirm = () => {
    if (renamingRoomId && newRoomName.trim()) {
      setRooms(prevRooms => 
        prevRooms?.map(room => 
          room.id === renamingRoomId 
            ? { ...room, name_hint: newRoomName.trim() }
            : room
        ) || null
      );
      setRenameDialogOpen(false);
      setRenamingRoomId(null);
      setNewRoomName('');
    }
  };

  const handleRenameCancel = () => {
    setRenameDialogOpen(false);
    setRenamingRoomId(null);
    setNewRoomName('');
  };

  const handleRemoveRoom = (roomId: string) => {
    setRooms(prevRooms => prevRooms?.filter(room => room.id !== roomId) || null);
    if (selectedRoomId === roomId) {
      setSelectedRoomId(null);
    }
    // Update metrics
    if (metrics && rooms) {
      const remainingRooms = rooms.filter(room => room.id !== roomId);
      setMetrics({
        ...metrics,
        rooms_count: remainingRooms.length
      });
    }
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
            Upload a JSON file with wall line segments, a PDF blueprint, or an image file (PNG, JPG, JPEG, BMP, TIFF) to detect rooms.
          </Typography>
          
          <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" component="h2">
                  Upload Blueprint
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<SettingsIcon />}
                  onClick={() => setParameterTuningOpen(true)}
                  size="small"
                >
                  Tune Parameters
                </Button>
              </Box>
              <FileUpload 
                onFileUpload={handleFileUpload} 
                onPdfUpload={handlePdfUpload}
                onImageUpload={handleImageUpload}
              />
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

          {(wallData || rooms) && (
            <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  {showJsonView ? 'JSON Payload' : showGraphView ? 'Graph Visualization' : 'Floorplan Visualization'}
                </Typography>
                <ToggleButtonGroup
                  value={showJsonView ? 'json' : showGraphView ? 'graph' : 'rooms'}
                  exclusive
                  onChange={(_, value) => {
                    if (value !== null) {
                      setShowJsonView(value === 'json');
                      setShowGraphView(value === 'graph');
                    }
                  }}
                  size="small"
                >
                  <ToggleButton value="rooms" aria-label="room view">
                    <ViewInArIcon sx={{ mr: 1 }} />
                    Rooms
                  </ToggleButton>
                  <ToggleButton value="graph" aria-label="graph view" disabled={!graphData}>
                    <AccountTreeIcon sx={{ mr: 1 }} />
                    Graph
                  </ToggleButton>
                  <ToggleButton value="json" aria-label="json view" disabled={!rooms || rooms.length === 0}>
                    <CodeIcon sx={{ mr: 1 }} />
                    JSON
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>

              {showJsonView ? (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    PRD-Compliant API Response Format:
                  </Typography>
                  <Paper 
                    elevation={1} 
                    sx={{ 
                      p: 2, 
                      backgroundColor: '#f5f5f5',
                      overflow: 'auto',
                      maxHeight: '600px',
                      fontFamily: 'monospace',
                      fontSize: '0.875rem'
                    }}
                  >
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(rooms, null, 2)}
                    </pre>
                  </Paper>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    This is the exact JSON payload returned by the /detect-rooms API endpoint (PRD Section 4.2)
                  </Typography>
                </Box>
              ) : showGraphView ? (
                <GraphVisualization 
                  graphData={graphData}
                  width={800}
                  height={600}
                />
              ) : (
                <>
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
                  
                  {selectedRoomId && rooms && (
                    <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Selected: {rooms.find(r => r.id === selectedRoomId)?.name_hint || selectedRoomId}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => handleRenameRoom(selectedRoomId)}
                        color="primary"
                        title="Rename room"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleRemoveRoom(selectedRoomId)}
                        color="error"
                        title="Remove room"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  )}
                </>
              )}
            </Paper>
          )}

          {/* Rename Dialog */}
          <Dialog open={renameDialogOpen} onClose={handleRenameCancel} maxWidth="sm" fullWidth>
            <DialogTitle>Rename Room</DialogTitle>
            <DialogContent>
              <TextField
                autoFocus
                margin="dense"
                label="Room Name"
                fullWidth
                variant="outlined"
                value={newRoomName}
                onChange={(e) => setNewRoomName(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleRenameConfirm();
                  }
                }}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={handleRenameCancel}>Cancel</Button>
              <Button onClick={handleRenameConfirm} variant="contained" disabled={!newRoomName.trim()}>
                Save
              </Button>
            </DialogActions>
          </Dialog>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
