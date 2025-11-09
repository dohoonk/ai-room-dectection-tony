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
  Tooltip,
  IconButton,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SettingsIcon from '@mui/icons-material/Settings';
import InfoIcon from '@mui/icons-material/Info';

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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      Gaussian Blur Kernel Size: {params.gaussianBlurKernelSize}
                    </Typography>
                    <Tooltip title="Controls the size of the blur filter applied to reduce image noise. Larger values (9-21) create more blur and remove more noise but may blur important details. Smaller values (3-5) preserve more detail but may keep noise. Must be an odd number. Recommended: 5 for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      Gaussian Blur Sigma: {params.gaussianBlurSigma.toFixed(1)}
                    </Typography>
                    <Tooltip title="Controls how much the blur spreads from the center. Higher values (2.5-5.0) create a wider, smoother blur effect. Lower values (0.5-1.0) create a tighter blur. Works together with kernel size - higher sigma with larger kernel creates stronger noise reduction. Recommended: 1.0 for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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
                <Box display="flex" alignItems="center" gap={1}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={params.useHistogramEqualization}
                        onChange={(e) => handleParamChange('useHistogramEqualization', e.target.checked)}
                      />
                    }
                    label="Use Histogram Equalization"
                  />
                  <Tooltip title="Improves image contrast by redistributing pixel intensities. Useful for images with poor lighting or low contrast. Enhances edge visibility but may over-enhance already high-contrast images. Enable for dim or washed-out blueprints. Disable if image is already high contrast." arrow>
                    <IconButton size="small">
                      <InfoIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      Low Threshold: {params.cannyLowThreshold}
                    </Typography>
                    <Tooltip title="Minimum edge strength to be considered a valid edge. Lower values (10-30) detect more weak edges and noise, creating more edge pixels. Higher values (100-200) only detect strong edges, reducing noise but potentially missing faint lines. Should be about 1/3 of the high threshold. Recommended: 50 for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      High Threshold: {params.cannyHighThreshold}
                    </Typography>
                    <Tooltip title="Strong edge threshold - edges above this are definitely kept. Lower values (50-100) keep more edges including weak ones. Higher values (200-300) only keep very strong edges, reducing false positives but potentially missing valid lines. Should be about 2-3x the low threshold. Recommended: 150 for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      Threshold: {params.houghThreshold}
                    </Typography>
                    <Tooltip title="Minimum number of edge points needed to form a line. Lower values (10-50) detect more lines including short or weak ones, but may create false positives. Higher values (150-300) only detect lines with strong edge support, reducing noise but potentially missing valid lines. Recommended: 100 for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      Min Line Length: {params.minLineLength}
                    </Typography>
                    <Tooltip title="Minimum length (in pixels) for a detected line segment. Shorter lines are discarded. Lower values (10-30) detect more short segments, useful for detailed blueprints but may include noise. Higher values (100-200) only keep long lines, reducing noise but potentially missing short wall segments. Recommended: 50 for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      Max Line Gap: {params.maxLineGap}
                    </Typography>
                    <Tooltip title="Maximum gap (in pixels) between line segments that can be connected into a single line. Useful for connecting broken lines. Lower values (5-10) keep lines separate, preserving detail. Higher values (20-50) connect more segments, creating longer continuous lines but may incorrectly join separate walls. Recommended: 10 for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      Min Length: {params.minLength}
                    </Typography>
                    <Tooltip title="Final minimum length filter for detected lines after all processing. Removes very short line segments that are likely noise. Lower values (5-15) keep more short segments, useful for detailed drawings. Higher values (50-100) filter out more short lines, reducing noise but potentially removing valid short walls. Recommended: 20 for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography gutterBottom>
                      Angle Tolerance (degrees): {params.angleTolerance}
                    </Typography>
                    <Tooltip title="Maximum angle difference (in degrees) for lines to be considered parallel or aligned. Used to merge nearly-parallel lines and filter lines by orientation. Lower values (1-3°) are strict, only merging very similar angles. Higher values (10-15°) are lenient, merging more lines but potentially combining non-parallel walls. Recommended: 5° for most images." arrow>
                      <IconButton size="small">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
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

