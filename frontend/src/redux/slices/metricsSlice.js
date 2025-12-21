// frontend/src/redux/slices/metricsSlice.js

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// Async thunk to fetch business metrics (tries multiple endpoints)
export const fetchBusinessMetrics = createAsyncThunk(
  'metrics/fetchBusinessMetrics',
  async (token, { rejectWithValue }) => {
    try {
      const backendUrl = import.meta.env.VITE_APP_API_URL || 'http://localhost:8000';
      const candidates = [
        '/api/v1/metrics/business_metrics',   // canonical (mounted under /api/v1/metrics)
        '/api/v1/metrics/business-metrics',
        '/api/v1/business-metrics'            // legacy frontend path
      ];

      for (const path of candidates) {
        const url = `${backendUrl}${path}`;
        try {
          const response = await fetch(url, {
            method: 'GET',
            headers: {
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
              'Content-Type': 'application/json',
            },
          });

          if (response.status === 404) {
            console.debug(`Metrics endpoint not found at ${url} (404), trying next candidate.`);
            continue; // try next candidate
          }

          if (!response.ok) {
            const text = await response.text();
            console.error('Metrics fetch error:', response.status, text);
            throw new Error(`HTTP error ${response.status} from ${url}`);
          }

          const data = await response.json();
          console.log('Metrics fetched successfully from', url, data);
          return data;
        } catch (err) {
          // If fetch failed due to network or non-404, propagate
          if (err instanceof Error && /HTTP error \d+/.test(err.message)) {
            // HTTP non-404 error, stop and reject
            return rejectWithValue({ message: err.message });
          }
          // network or other error; try next candidate unless it's the last
          console.warn(`Request to ${url} failed, trying next candidate.`, err);
          continue;
        }
      }

      // All candidates returned 404 / failed
      console.log('No business metrics found on any candidate endpoints (404)');
      return null;
    } catch (error) {
      console.error('Metrics fetch exception:', error);
      return rejectWithValue(error.message || 'Failed to fetch metrics');
    }
  }
);

const initialState = {
  metricsData: null,
  loading: false,
  error: null,
};

const metricsSlice = createSlice({
  name: 'metrics',
  initialState,
  reducers: {
    clearMetricsError: (state) => {
      state.error = null;
    },
    resetMetrics: (state) => {
      state.metricsData = null;
      state.loading = false;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBusinessMetrics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBusinessMetrics.fulfilled, (state, action) => {
        state.loading = false;
        state.metricsData = action.payload;
      })
      .addCase(fetchBusinessMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error;
      });
  },
});

export const { clearMetricsError, resetMetrics } = metricsSlice.actions;
export default metricsSlice.reducer;