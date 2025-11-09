import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Slider,
  TextField,
  Typography,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  Stack,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SettingsIcon from '@mui/icons-material/Settings';

export interface ImageProcessingParameters {
  // Preprocessing
  gaussianBlurKernelSize: number;
  gaussianBlurSigma: number;
  useHistogramEqualization: boolean;
  
  // Edge Detection (Canny)
  cannyLowThreshold: number;
  cannyHighThreshold: number;
  
  // Line Detection (Hough)
  houghThreshold: number;
  minLineLength: number;
  maxLineGap: number;
  
  // Line Filtering
  minLength: number;
  angleTolerance: number;
}

const DEFAULT_PARAMETERS: ImageProcessingParameters = {
  gaussianBlurKernelSize: 5,
  gaussianBlurSigma: 1.0,
  useHistogramEqualization: true,
  cannyLowThreshold: 50,
  cannyHighThreshold: 150,
  houghThreshold: 100,
  minLineLength: 50.0,
  maxLineGap: 10.0,
  minLength: 20.0,
  angleTolerance: 5.0,
};

const STORAGE_KEY = 'imageProcessingParameters';

interface ParameterTuningProps {
  open: boolean;
  onClose: () => void;
  onApply: (params: ImageProcessingParameters) => void;
  currentParams?: ImageProcessingParameters;
}

const ParameterTuning: React.FC<ParameterTuningProps> = ({
  open,
  onClose,
  onApply,
  currentParams,
}) => {
  const [params, setParams] = useState<ImageProcessingParameters>(
    currentParams || DEFAULT_PARAMETERS
  );

  // Load saved parameters from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setParams({ ...DEFAULT_PARAMETERS, ...parsed });
      } catch (e) {
        console.warn('Failed to parse saved parameters:', e);
      }
    }
  }, []);

  // Update params when currentParams prop changes
  useEffect(() => {
    if (currentParams) {
      setParams(currentParams);
    }
  }, [currentParams]);

  const handleParamChange = (key: keyof ImageProcessingParameters, value: number | boolean) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    setParams(DEFAULT_PARAMETERS);
  };

  const handleApply = () => {
    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(params));
    onApply(params);
    onClose();
  };

  const handleCancel = () => {
    // Restore from currentParams or saved
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setParams({ ...DEFAULT_PARAMETERS, ...parsed });
      } catch (e) {
        setParams(DEFAULT_PARAMETERS);
      }
    } else if (currentParams) {
      setParams(currentParams);
    } else {
      setParams(DEFAULT_PARAMETERS);
    }
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <SettingsIcon />
          <Typography variant="h6">Image Processing Parameters</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {/* Preprocessing Section */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" fontWeight="bold">
                Preprocessing
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Stack spacing={3}>
                <Box>
                  <Typography gutterBottom>
                    Gaussian Blur Kernel Size: {params.gaussianBlurKernelSize}
                  </Typography>
                  <Slider
                    value={params.gaussianBlurKernelSize}
                    onChange={(_, value) => {
                      // Ensure odd number (required by OpenCV)
                      const oddValue = Math.round(value as number);
                      const finalValue = oddValue % 2 === 0 ? oddValue + 1 : oddValue;
                      handleParamChange('gaussianBlurKernelSize', Math.max(3, Math.min(21, finalValue)));
                    }}
                    min={3}
                    max={21}
                    step={2}
                    marks={[
                      { value: 3, label: '3' },
                      { value: 5, label: '5' },
                      { value: 9, label: '9' },
                      { value: 15, label: '15' },
                      { value: 21, label: '21' },
                    ]}
                  />
                </Box>
                <Box>
                  <Typography gutterBottom>
                    Gaussian Blur Sigma: {params.gaussianBlurSigma.toFixed(1)}
                  </Typography>
                  <Slider
                    value={params.gaussianBlurSigma}
                    onChange={(_, value) => handleParamChange('gaussianBlurSigma', value as number)}
                    min={0.5}
                    max={5.0}
                    step={0.1}
                    marks={[
                      { value: 0.5, label: '0.5' },
                      { value: 1.0, label: '1.0' },
                      { value: 2.5, label: '2.5' },
                      { value: 5.0, label: '5.0' },
                    ]}
                  />
                </Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={params.useHistogramEqualization}
                      onChange={(e) => handleParamChange('useHistogramEqualization', e.target.checked)}
                    />
                  }
                  label="Use Histogram Equalization"
                />
              </Stack>
            </AccordionDetails>
          </Accordion>

          {/* Edge Detection Section */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" fontWeight="bold">
                Edge Detection (Canny)
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Stack spacing={3}>
                <Box>
                  <Typography gutterBottom>
                    Low Threshold: {params.cannyLowThreshold}
                  </Typography>
                  <Slider
                    value={params.cannyLowThreshold}
                    onChange={(_, value) => handleParamChange('cannyLowThreshold', value as number)}
                    min={10}
                    max={200}
                    step={5}
                    marks={[
                      { value: 10, label: '10' },
                      { value: 50, label: '50' },
                      { value: 100, label: '100' },
                      { value: 150, label: '150' },
                      { value: 200, label: '200' },
                    ]}
                  />
                </Box>
                <Box>
                  <Typography gutterBottom>
                    High Threshold: {params.cannyHighThreshold}
                  </Typography>
                  <Slider
                    value={params.cannyHighThreshold}
                    onChange={(_, value) => handleParamChange('cannyHighThreshold', value as number)}
                    min={50}
                    max={300}
                    step={5}
                    marks={[
                      { value: 50, label: '50' },
                      { value: 150, label: '150' },
                      { value: 200, label: '200' },
                      { value: 300, label: '300' },
                    ]}
                  />
                </Box>
              </Stack>
            </AccordionDetails>
          </Accordion>

          {/* Line Detection Section */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" fontWeight="bold">
                Line Detection (Hough Transform)
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Stack spacing={3}>
                <Box>
                  <Typography gutterBottom>
                    Threshold: {params.houghThreshold}
                  </Typography>
                  <Slider
                    value={params.houghThreshold}
                    onChange={(_, value) => handleParamChange('houghThreshold', value as number)}
                    min={10}
                    max={300}
                    step={5}
                    marks={[
                      { value: 10, label: '10' },
                      { value: 50, label: '50' },
                      { value: 100, label: '100' },
                      { value: 200, label: '200' },
                      { value: 300, label: '300' },
                    ]}
                  />
                </Box>
                <Box>
                  <Typography gutterBottom>
                    Min Line Length: {params.minLineLength}
                  </Typography>
                  <Slider
                    value={params.minLineLength}
                    onChange={(_, value) => handleParamChange('minLineLength', value as number)}
                    min={10}
                    max={200}
                    step={5}
                    marks={[
                      { value: 10, label: '10' },
                      { value: 50, label: '50' },
                      { value: 100, label: '100' },
                      { value: 150, label: '150' },
                      { value: 200, label: '200' },
                    ]}
                  />
                </Box>
                <Box>
                  <Typography gutterBottom>
                    Max Line Gap: {params.maxLineGap}
                  </Typography>
                  <Slider
                    value={params.maxLineGap}
                    onChange={(_, value) => handleParamChange('maxLineGap', value as number)}
                    min={5}
                    max={50}
                    step={1}
                    marks={[
                      { value: 5, label: '5' },
                      { value: 10, label: '10' },
                      { value: 20, label: '20' },
                      { value: 30, label: '30' },
                      { value: 50, label: '50' },
                    ]}
                  />
                </Box>
              </Stack>
            </AccordionDetails>
          </Accordion>

          {/* Line Filtering Section */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" fontWeight="bold">
                Line Filtering
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Stack spacing={3}>
                <Box>
                  <Typography gutterBottom>
                    Min Length: {params.minLength}
                  </Typography>
                  <Slider
                    value={params.minLength}
                    onChange={(_, value) => handleParamChange('minLength', value as number)}
                    min={5}
                    max={100}
                    step={5}
                    marks={[
                      { value: 5, label: '5' },
                      { value: 20, label: '20' },
                      { value: 50, label: '50' },
                      { value: 100, label: '100' },
                    ]}
                  />
                </Box>
                <Box>
                  <Typography gutterBottom>
                    Angle Tolerance (degrees): {params.angleTolerance}
                  </Typography>
                  <Slider
                    value={params.angleTolerance}
                    onChange={(_, value) => handleParamChange('angleTolerance', value as number)}
                    min={1}
                    max={15}
                    step={0.5}
                    marks={[
                      { value: 1, label: '1°' },
                      { value: 5, label: '5°' },
                      { value: 10, label: '10°' },
                      { value: 15, label: '15°' },
                    ]}
                  />
                </Box>
              </Stack>
            </AccordionDetails>
          </Accordion>
        </Stack>
      </DialogContent>
      <Divider />
      <DialogActions>
        <Button onClick={handleReset} color="secondary">
          Reset to Defaults
        </Button>
        <Button onClick={handleCancel}>Cancel</Button>
        <Button onClick={handleApply} variant="contained" color="primary">
          Apply
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ParameterTuning;
export { DEFAULT_PARAMETERS, STORAGE_KEY };

