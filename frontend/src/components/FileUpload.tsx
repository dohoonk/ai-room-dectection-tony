import React, { useRef } from 'react';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import UploadFileIcon from '@mui/icons-material/UploadFile';

interface FileUploadProps {
  onFileUpload: (data: any[]) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [fileName, setFileName] = React.useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setError(null);
    setFileName(file.name);

    // Validate file type
    if (!file.name.endsWith('.json')) {
      setError('Please upload a JSON file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const data = JSON.parse(text);
        
        // Validate data structure
        if (!Array.isArray(data)) {
          setError('JSON must contain an array of wall segments');
          return;
        }

        // Validate wall segment structure
        for (const segment of data) {
          if (!segment.type || !segment.start || !segment.end) {
            setError('Invalid wall segment structure. Each segment must have type, start, and end fields.');
            return;
          }
        }

        onFileUpload(data);
      } catch (err) {
        setError(`Error parsing JSON: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    };

    reader.onerror = () => {
      setError('Error reading file');
    };

    reader.readAsText(file);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Box>
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      <Button
        variant="contained"
        component="span"
        startIcon={<UploadFileIcon />}
        onClick={handleButtonClick}
        size="large"
      >
        Upload JSON File
      </Button>
      {fileName && (
        <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
          Selected: {fileName}
        </Typography>
      )}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default FileUpload;

