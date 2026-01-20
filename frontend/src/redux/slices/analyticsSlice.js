import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

/**
 * Analytics data management slice
 * Handles revenue metrics, transaction analytics, and business insights
 *
 * Optimized for memory efficiency by adding specific reset actions
 * and encouraging selective data loading.
 */

// Async thunks for analytics API calls (no changes needed here, as thunks
// define *what* to fetch, not *how much* to store, which is handled in reducers)
export const fetchDashboardMetrics = createAsyncThunk(
  'analytics/fetchDashboardMetrics',
  async ({ period = '30d' }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/v1/analytics/dashboard?period=${period}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch metrics');
    }
  }
);

export const fetchRevenueAnalytics = createAsyncThunk(
  'analytics/fetchRevenueAnalytics',
  async ({ startDate, endDate, granularity = 'daily' }, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/v1/analytics/revenue', {
        params: { startDate, endDate, granularity }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch revenue data');
    }
  }
);

export const fetchTransactionAnalytics = createAsyncThunk(
  'analytics/fetchTransactionAnalytics',
  async ({ period = '30d', category = 'all', page = 1, limit = 50 }, { rejectWithValue }) => {
    try {
      // Added pagination parameters to the API call
      const response = await api.get('/api/v1/analytics/transactions', {
        params: { period, category, page, limit }
      });
      return response.data; // Expecting { transactions: [...], totalCount: N }
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch transaction data');
    }
  }
);

export const fetchCustomerAnalytics = createAsyncThunk(
  'analytics/fetchCustomerAnalytics',
  async ({ period = '30d', page = 1, limit = 50 }, { rejectWithValue }) => {
    try {
      // Added pagination parameters to the API call
      const response = await api.get(`/api/v1/analytics/customers?period=${period}&page=${page}&limit=${limit}`);
      return response.data; // Expecting { customers: [...], totalCount: N }
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch customer data');
    }
  }
);

export const fetchPredictiveInsights = createAsyncThunk(
  'analytics/fetchPredictiveInsights',
  async ({ horizon = '90d' }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/api/v1/analytics/predictions?horizon=${horizon}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch predictions');
    }
  }
);

// Initial state
const initialState = {
  // Dashboard metrics (generally small)
  dashboardMetrics: {
    totalRevenue: 0,
    totalTransactions: 0,
    averageOrderValue: 0,
    customerGrowth: 0,
    conversionRate: 0,
    monthlyRecurring: 0,
    loading: false,
    error: null,
    lastUpdated: null
  },

  // Revenue analytics - `timeSeries` is the main concern here for size
  revenueData: {
    timeSeries: [], // This array can grow very large if not managed
    breakdown: {},
    trends: {},
    loading: false,
    error: null
  },

  // Transaction analytics - `volume` (if it's a list of transactions) and `refunds` are key concerns
  transactionData: {
    volume: [], // If this represents individual transactions, it needs pagination
    categories: [],
    paymentMethods: [],
    refunds: [],
    totalTransactionsCount: 0, // Added for pagination
    loading: false,
    error: null
  },

  // Customer analytics - `acquisition` (if it's a list of customers) and `segments` are key concerns
  customerData: {
    acquisition: [], // If this represents individual customers, it needs pagination
    retention: {},
    segments: [],
    totalCustomerCount: 0, // Added for pagination
    lifetime_value: {},
    loading: false,
    error: null
  },

  // Predictive insights - `revenue` (time series) and `recommendations` can be large
  predictions: {
    revenue: [],
    trends: [],
    recommendations: [],
    confidence: 0,
    loading: false,
    error: null
  },

  // Filters and settings (generally small)
  filters: {
    dateRange: '30d',
    currency: 'USD',
    granularity: 'daily'
  },

  // Real-time updates (generally small)
  realTimeData: {
    enabled: false,
    lastPing: null,
    connectionStatus: 'disconnected'
  }
};

// Analytics slice
const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    // Filter and settings actions
    updateFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },

    // Real-time data actions
    enableRealTimeUpdates: (state) => {
      state.realTimeData.enabled = true;
      state.realTimeData.connectionStatus = 'connecting';
    },
    disableRealTimeUpdates: (state) => {
      state.realTimeData.enabled = false;
      state.realTimeData.connectionStatus = 'disconnected';
    },
    updateRealTimeStatus: (state, action) => {
      state.realTimeData.connectionStatus = action.payload;
      state.realTimeData.lastPing = new Date().toISOString();
    },

    // Clear errors
    clearErrors: (state) => {
      state.dashboardMetrics.error = null;
      state.revenueData.error = null;
      state.transactionData.error = null;
      state.customerData.error = null;
      state.predictions.error = null;
    },

    // Specific reset actions for memory management
    // Resets the entire analytics slice to its initial state
    resetAnalytics: () => initialState,
    // Resets only revenue data
    resetRevenueData: (state) => {
      state.revenueData = initialState.revenueData;
    },
    // Resets only transaction data
    resetTransactionData: (state) => {
      state.transactionData = initialState.transactionData;
    },
    // Resets only customer data
    resetCustomerData: (state) => {
      state.customerData = initialState.customerData;
    },
    // Resets only predictions data
    resetPredictions: (state) => {
      state.predictions = initialState.predictions;
    },
    // NEW: Action to set analytics data from a direct API response
  setAnalyticsData: (state, action) => {
    const data = action.payload;
    
    // Update dashboard metrics from the API response
    state.dashboardMetrics.totalRevenue = data.totalRevenue ?? 0;
    state.dashboardMetrics.totalTransactions = data.totalTransactions ?? 0;
    state.dashboardMetrics.averageOrderValue = data.averageOrderValue ?? 0;
    state.dashboardMetrics.growthRate = data.growthRate ?? 0;
    state.dashboardMetrics.riskScore = data.riskScore ?? 0;
    state.dashboardMetrics.riskLevel = data.riskLevel ?? 'low';
    state.dashboardMetrics.lastUpdated = new Date().toISOString();
    state.dashboardMetrics.error = null;
    state.dashboardMetrics.loading = false;
    
    // Store chart data if available
    if (data.chartData) {
      state.revenueData.timeSeries = data.chartData;
    }
    
    // Store marketing ROI if available
    if (data.marketingRoi) {
      state.revenueData.breakdown = data.marketingRoi;
    }
  },
    // Resets only dashboard metrics (often doesn't need to be reset due to small size)
    resetDashboardMetrics: (state) => {
        state.dashboardMetrics = initialState.dashboardMetrics;
    }
  },

  extraReducers: (builder) => {
    builder
      // Dashboard metrics cases
      .addCase(fetchDashboardMetrics.pending, (state) => {
        state.dashboardMetrics.loading = true;
        state.dashboardMetrics.error = null;
      })
      .addCase(fetchDashboardMetrics.fulfilled, (state, action) => {
        state.dashboardMetrics.loading = false;
        // Directly update properties instead of spreading the whole payload
        // This assumes action.payload directly contains the new metric values
        state.dashboardMetrics.totalRevenue = action.payload.totalRevenue ?? 0;
        state.dashboardMetrics.totalTransactions = action.payload.totalTransactions ?? 0;
        state.dashboardMetrics.averageOrderValue = action.payload.averageOrderValue ?? 0;
        state.dashboardMetrics.customerGrowth = action.payload.customerGrowth ?? 0;
        state.dashboardMetrics.conversionRate = action.payload.conversionRate ?? 0;
        state.dashboardMetrics.monthlyRecurring = action.payload.monthlyRecurring ?? 0;
        state.dashboardMetrics.lastUpdated = new Date().toISOString();
        state.dashboardMetrics.error = null;
      })
      .addCase(fetchDashboardMetrics.rejected, (state, action) => {
        state.dashboardMetrics.loading = false;
        state.dashboardMetrics.error = action.payload;
      })

      // Revenue analytics cases - always replace timeSeries when new data is fetched
      .addCase(fetchRevenueAnalytics.pending, (state) => {
        state.revenueData.loading = true;
        state.revenueData.error = null;
      })
      .addCase(fetchRevenueAnalytics.fulfilled, (state, action) => {
        state.revenueData.loading = false;
        // IMPORTANT: Replace the entire array to prevent continuous growth
        state.revenueData.timeSeries = action.payload.timeSeries || [];
        state.revenueData.breakdown = action.payload.breakdown || {};
        state.revenueData.trends = action.payload.trends || {};
        state.revenueData.error = null;
      })
      .addCase(fetchRevenueAnalytics.rejected, (state, action) => {
        state.revenueData.loading = false;
        state.revenueData.error = action.payload;
      })

      // Transaction analytics cases - manage paginated data
      .addCase(fetchTransactionAnalytics.pending, (state) => {
        state.transactionData.loading = true;
        state.transactionData.error = null;
      })
      .addCase(fetchTransactionAnalytics.fulfilled, (state, action) => {
        state.transactionData.loading = false;
        // Assuming action.payload contains { transactions: [...], totalCount: N }
        // For initial load or new filters, replace. For "load more", append.
        // This example replaces for simplicity, you'd add logic for appending if needed
        state.transactionData.volume = action.payload.transactions || []; // Renamed from 'volume' if it's the list
        state.transactionData.totalTransactionsCount = action.payload.totalCount || 0;
        state.transactionData.categories = action.payload.categories || [];
        state.transactionData.paymentMethods = action.payload.paymentMethods || [];
        state.transactionData.refunds = action.payload.refunds || []; // This would also ideally be paginated if large
        state.transactionData.error = null;
      })
      .addCase(fetchTransactionAnalytics.rejected, (state, action) => {
        state.transactionData.loading = false;
        state.transactionData.error = action.payload;
      })

      // Customer analytics cases - manage paginated data
      .addCase(fetchCustomerAnalytics.pending, (state) => {
        state.customerData.loading = true;
        state.customerData.error = null;
      })
      .addCase(fetchCustomerAnalytics.fulfilled, (state, action) => {
        state.customerData.loading = false;
        // Assuming action.payload contains { customers: [...], totalCount: N }
        state.customerData.acquisition = action.payload.customers || []; // Renamed from 'acquisition' if it's the list
        state.customerData.totalCustomerCount = action.payload.totalCount || 0;
        state.customerData.retention = action.payload.retention || {};
        state.customerData.segments = action.payload.segments || [];
        state.customerData.lifetime_value = action.payload.lifetime_value || {};
        state.customerData.error = null;
      })
      .addCase(fetchCustomerAnalytics.rejected, (state, action) => {
        state.customerData.loading = false;
        state.customerData.error = action.payload;
      })

      // Predictive insights cases
      .addCase(fetchPredictiveInsights.pending, (state) => {
        state.predictions.loading = true;
        state.predictions.error = null;
      })
      .addCase(fetchPredictiveInsights.fulfilled, (state, action) => {
        state.predictions.loading = false;
        // Replace full prediction data
        state.predictions.revenue = action.payload.revenue || [];
        state.predictions.trends = action.payload.trends || [];
        state.predictions.recommendations = action.payload.recommendations || [];
        state.predictions.confidence = action.payload.confidence ?? 0;
        state.predictions.error = null;
      })
      .addCase(fetchPredictiveInsights.rejected, (state, action) => {
        state.predictions.loading = false;
        state.predictions.error = action.payload;
      });
  },
});

// Export actions
export const {
  updateFilters,
  enableRealTimeUpdates,
  disableRealTimeUpdates,
  updateRealTimeStatus,
  clearErrors,
  resetAnalytics,
  resetRevenueData,
  resetTransactionData,
  resetCustomerData,
  resetPredictions,
  resetDashboardMetrics,
  setAnalyticsData  // ADD THIS LINE
} = analyticsSlice.actions;


// Selectors
export const selectDashboardMetrics = (state) => state.analytics.dashboardMetrics;
export const selectRevenueData = (state) => state.analytics.revenueData;
export const selectTransactionData = (state) => state.analytics.transactionData;
export const selectCustomerData = (state) => state.analytics.customerData;
export const selectPredictions = (state) => state.analytics.predictions;
export const selectAnalyticsFilters = (state) => state.analytics.filters;
export const selectRealTimeStatus = (state) => state.analytics.realTimeData;

export default analyticsSlice.reducer;