import React from 'react';
import { Card, CardContent, Typography, Box, Stack } from '@mui/material';

export interface MetricsDisplayProps {
  roomsCount: number;
  processingTime?: number; // in seconds
  confidenceScore?: number; // 0.00 to 1.00
}

const MetricsDisplay: React.FC<MetricsDisplayProps> = ({
  roomsCount,
  processingTime,
  confidenceScore,
}) => {
  const formatTime = (seconds?: number): string => {
    if (seconds === undefined || seconds === null) {
      return 'N/A';
    }
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)} ms`;
    }
    return `${seconds.toFixed(2)} seconds`;
  };

  const formatConfidence = (score?: number): string => {
    if (score === undefined || score === null) {
      return 'N/A';
    }
    return `${(score * 100).toFixed(0)}%`;
  };

  const getConfidenceColor = (score?: number): string => {
    if (score === undefined || score === null) {
      return 'text.secondary';
    }
    if (score >= 0.8) {
      return 'success.main';
    } else if (score >= 0.6) {
      return 'warning.main';
    } else {
      return 'error.main';
    }
  };

  return (
    <Card elevation={2}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Detection Metrics
        </Typography>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          sx={{ mt: 1 }}
        >
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Rooms Detected
            </Typography>
            <Typography variant="h5" component="div">
              {roomsCount}
            </Typography>
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Processing Time
            </Typography>
            <Typography variant="h5" component="div">
              {formatTime(processingTime)}
            </Typography>
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Confidence Score
            </Typography>
            <Typography
              variant="h5"
              component="div"
              color={getConfidenceColor(confidenceScore)}
            >
              {formatConfidence(confidenceScore)}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default MetricsDisplay;

