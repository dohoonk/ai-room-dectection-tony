import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import FileUpload from './components/FileUpload';
import WallVisualization from './components/WallVisualization';
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
  const [wallData, setWallData] = React.useState<any[] | null>(null);

  const handleFileUpload = (data: any[]) => {
    setWallData(data);
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

          {wallData && (
            <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Floorplan Visualization
              </Typography>
              <WallVisualization walls={wallData} />
            </Paper>
          )}
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
