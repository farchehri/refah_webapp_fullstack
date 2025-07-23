// src/components/DashboardCharts.tsx
// REMOVED: import React, { useEffect, useState } from 'react';
import { useEffect, useState } from 'react'; // Keep these hooks
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

// --- CRITICAL FIX 1: Define the data row interface ---
interface BigQueryDataRow {
  // Adjust these properties and types based on your actual BigQuery data
  // Example:
  id?: string;
  category: string;
  value: number;
  date?: string; // Optional property
  // Add all properties that your BigQuery view might return
}

function DashboardCharts() {
  // --- CRITICAL FIX 2: Explicitly type the useState for data ---
  const [data, setData] = useState<BigQueryDataRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const FLASK_API_BASE_URL = import.meta.env.VITE_FLASK_API_URL;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${FLASK_API_BASE_URL}/api/charts_data`);
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.details || 'Failed to fetch dashboard data');
        }
        const result: BigQueryDataRow[] = await response.json(); // Explicitly type the parsed JSON
        setData(result);
      } catch (err: unknown) { // --- CRITICAL FIX 3: Type guard for 'err' ---
        console.error('Error fetching dashboard data:', err);
        let errorMessage = 'An unknown error occurred.';
        if (err instanceof Error) {
          errorMessage = err.message;
        } else if (typeof err === 'string') {
          errorMessage = err;
        }
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">Error: {error}</Alert>;
  if (data.length === 0) return <Typography>No data available.</Typography>;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Sample Data (from Flask API)</Typography>
      {/* You'll replace this with actual charts later, just showing data structure now */}
      <pre style={{ overflowX: 'auto', whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
        {JSON.stringify(data.slice(0, 5), null, 2)}
      </pre>
    </Box>
  );
}

export default DashboardCharts;