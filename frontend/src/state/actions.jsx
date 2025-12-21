/**
 * Redux Action Creators for AI-Embedded Finance Platform
 * Handles async operations and dispatches actions to appropriate slices
 *
 * @fileoverview Centralized action creators for user auth, analytics, and finance operations
 * @author Senior Full-Stack Developer
 * @version 1.0.0
 */

import { createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';
//import { paymentService } from '../services/paymentService.jsx'; // ENSURE THIS HAS .jsx EXTENSION
import { getAnalytics, getCustomerAnalytics } from '../services/analyticsService';

// ============================================================================
// AUTH ACTIONS
// ============================================================================

/**
 * Async thunk for user login
 * @param {Object} credentials - User login credentials
 * @param {string} credentials.email - User email
 * @param {string} credentials.password - User password
 */
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await api.post('/auth/login', credentials);

      // Store token in localStorage for persistence
      if (response.data.access_token) {
        localStorage.setItem('accessToken', response.data.access_token);
        localStorage.setItem('refreshToken', response.data.refresh_token);

        // Set default auth header for future requests
        api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      }

      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Login failed. Please try again.'
      );
    }
  }
);

/**
 * Async thunk for user registration
 * @param {Object} userData - User registration data
 */
export const registerUser = createAsyncThunk(
  'auth/registerUser',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await api.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Registration failed. Please try again.'
      );
    }
  }
);

/**
 * Async thunk for user logout
 */
export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { rejectWithValue }) => {
    try {
      await api.post('/auth/logout');

      // Clear stored tokens
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');

      // Remove auth header
      delete api.defaults.headers.common['Authorization'];

      return null;
    } catch (error) {
      // Even if logout fails on server, clear local storage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      delete api.defaults.headers.common['Authorization'];

      return rejectWithValue(
        error.response?.data?.message || 'Logout failed'
      );
    }
  }
);

/**
 * Async thunk for refreshing auth token
 */
export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken
      });

      localStorage.setItem('accessToken', response.data.access_token);
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;

      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Token refresh failed'
      );
    }
  }
);

/**
 * Async thunk for fetching current user profile
 */
export const fetchUserProfile = createAsyncThunk(
  'auth/fetchUserProfile',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch user profile'
      );
    }
  }
);

// ============================================================================
// ANALYTICS ACTIONS
// ============================================================================

/**
 * Async thunk for fetching dashboard analytics
 * @param {Object} params - Query parameters
 * @param {string} params.period - Time period (7d, 30d, 90d, 1y)
 * @param {string} params.granularity - Data granularity (hour, day, week, month)
 */
export const fetchDashboardAnalytics = createAsyncThunk(
  'analytics/fetchDashboardAnalytics',
  async (params = {}, { rejectWithValue }) => {
    try {
      const response = await getAnalytics(params); // Use direct function call
      return response.data || response; // Handle both wrapped and direct responses
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch dashboard analytics'
      );
    }
  }
);

/**
 * Async thunk for fetching revenue analytics
 * @param {Object} filters - Revenue filters
 */
export const fetchRevenueAnalytics = createAsyncThunk(
  'analytics/fetchRevenueAnalytics',
  async (filters, { rejectWithValue }) => {
    try {
      const response = await getCustomerAnalytics(filters); // Use direct function call
      return response.data || response; // Handle both wrapped and direct responses
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch revenue analytics'
      );
    }
  }
);

/**
 * Async thunk for fetching customer analytics
 * @param {Object} filters - Customer filters
 */
export const fetchCustomerAnalytics = createAsyncThunk(
  'analytics/fetchCustomerAnalytics',
  async (filters, { rejectWithValue }) => {
    try {
      const response = await getCustomerAnalytics(filters); // Use direct function call
      return response.data || response; // Handle both wrapped and direct responses
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch customer analytics'
      );
    }
  }
);

/**
 * Async thunk for fetching transaction analytics
 * @param {Object} filters - Transaction filters
 */
export const fetchTransactionAnalytics = createAsyncThunk(
  'analytics/fetchTransactionAnalytics',
  async (filters, { rejectWithValue }) => {
    try {
      const response = await getAnalytics(filters); // Use appropriate function for transactions
      return response.data || response; // Handle both wrapped and direct responses
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch transaction analytics'
      );
    }
  }
);

/**
 * Async thunk for fetching AI-powered insights
 * @param {Object} params - Insight parameters
 */
export const fetchAIInsights = createAsyncThunk(
  'analytics/fetchAIInsights',
  async (params, { rejectWithValue }) => {
    try {
      const response = await api.post('/insights/generate', params);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch AI insights'
      );
    }
  }
);

/**
 * Async thunk for updating analytics filters
 * @param {Object} filters - New filter values
 */
export const updateAnalyticsFilters = createAsyncThunk(
  'analytics/updateFilters',
  async (filters, { getState, dispatch }) => {
    // Update filters and refetch relevant data
    const state = getState();
    const currentFilters = state.analytics.filters;
    const newFilters = { ...currentFilters, ...filters };

    // Trigger data refetch based on active view
    if (state.analytics.activeView === 'revenue') {
      dispatch(fetchRevenueAnalytics(newFilters));
    } else if (state.analytics.activeView === 'customers') {
      dispatch(fetchCustomerAnalytics(newFilters));
    } else if (state.analytics.activeView === 'transactions') {
      dispatch(fetchTransactionAnalytics(newFilters));
    }

    return newFilters;
  }
);

// ============================================================================
// FINANCE ACTIONS
// ============================================================================

/**
 * Async thunk for fetching payment methods
 */
export const fetchPaymentMethods = createAsyncThunk(
  'finance/fetchPaymentMethods',
  async (_, { rejectWithValue }) => {
    try {
      const response = await paymentService.getPaymentMethods();
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch payment methods'
      );
    }
  }
);

/**
 * Async thunk for processing a payment
 * @param {Object} paymentData - Payment information
 */
export const processPayment = createAsyncThunk(
  'finance/processPayment',
  async (paymentData, { rejectWithValue }) => {
    try {
      const response = await paymentService.processPayment(paymentData);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Payment processing failed'
      );
    }
  }
);

/**
 * Async thunk for fetching transaction history
 * @param {Object} params - Query parameters
 */
export const fetchTransactionHistory = createAsyncThunk(
  'finance/fetchTransactionHistory',
  async (params, { rejectWithValue }) => {
    try {
      const response = await paymentService.getTransactionHistory(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch transaction history'
      );
    }
  }
);

/**
 * Async thunk for fetching financing options
 */
export const fetchFinancingOptions = createAsyncThunk(
  'finance/fetchFinancingOptions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/financing/options');
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch financing options'
      );
    }
  }
);

/**
 * Async thunk for applying for financing
 * @param {Object} applicationData - Financing application data
 */
export const applyForFinancing = createAsyncThunk(
  'finance/applyForFinancing',
  async (applicationData, { rejectWithValue }) => {
    try {
      const response = await api.post('/financing/apply', applicationData);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Financing application failed'
      );
    }
  }
);

/**
 * Async thunk for fetching financing applications
 */
export const fetchFinancingApplications = createAsyncThunk(
  'finance/fetchFinancingApplications',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/financing/applications');
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch financing applications'
      );
    }
  }
);

/**
 * Async thunk for syncing payment data from external sources
 * @param {string} source - Payment source (stripe, shopify, quickbooks)
 */
export const syncPaymentData = createAsyncThunk(
  'finance/syncPaymentData',
  async (source, { rejectWithValue }) => {
    try {
      const response = await api.post(`/payments/sync/${source}`);
      return { source, ...response.data };
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || `Failed to sync ${source} data`
      );
    }
  }
);

/**
 * Async thunk for fetching account balance
 */
export const fetchAccountBalance = createAsyncThunk(
  'finance/fetchAccountBalance',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/payments/balance');
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch account balance'
      );
    }
  }
);

// ============================================================================
// AI CHAT ACTIONS
// ============================================================================

/**
 * Async thunk for sending message to AI agent
 * @param {Object} messageData - Message data
 * @param {string} messageData.message - User message
 * @param {string} messageData.context - Current context/view
 */
export const sendAIMessage = createAsyncThunk(
  'ai/sendMessage',
  async (messageData, { rejectWithValue, getState }) => {
    try {
      const state = getState();

      // Include relevant context from current state
      const contextData = {
        ...messageData,
        userProfile: state.auth.user,
        currentView: state.analytics.activeView,
        filters: state.analytics.filters,
        recentTransactions: state.finance.transactions?.slice(0, 10) || []
      };

      const response = await api.post('/ai/chat', contextData);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'AI chat failed'
      );
    }
  }
);

/**
 * Async thunk for fetching AI chat history
 */
export const fetchAIChatHistory = createAsyncThunk(
  'ai/fetchChatHistory',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/ai/chat/history');
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.message || 'Failed to fetch chat history'
      );
    }
  }
);

// ============================================================================
// UTILITY ACTIONS
// ============================================================================

/**
 * Async thunk for initializing app data
 * Fetches all necessary data when app loads
 */
export const initializeApp = createAsyncThunk(
  'app/initialize',
  async (_, { dispatch, rejectWithValue }) => {
    try {
      // Check for existing auth token
      const token = localStorage.getItem('accessToken');
      if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

        // Fetch user profile and initial data
        await dispatch(fetchUserProfile()).unwrap();

        // Fetch initial dashboard data
        await Promise.all([
          dispatch(fetchDashboardAnalytics()),
          //dispatch(fetchPaymentMethods()),
          dispatch(fetchAccountBalance())
        ]);
      }

      return { initialized: true };
    } catch (error) {
      // If token is invalid, clear it
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      delete api.defaults.headers.common['Authorization'];

      return rejectWithValue('App initialization failed');
    }
  }
);

/**
 * Action creator for clearing all error states
 */
export const clearErrors = () => ({
  type: 'CLEAR_ALL_ERRORS'
});

/**
 * Action creator for setting global loading state
 * @param {boolean} isLoading - Loading state
 */
export const setGlobalLoading = (isLoading) => ({
  type: 'SET_GLOBAL_LOADING',
  payload: isLoading
});

/**
 * Action creator for setting loading state
 * @param {boolean} isLoading - Loading state
 */
export const setLoading = (isLoading) => ({
  type: 'SET_LOADING',
  payload: isLoading
});

/**
 * Action creator for setting payments data
 * @param {Array} payments - Payments array
 */
export const setPayments = (payments) => ({
  type: 'SET_PAYMENTS',
  payload: payments
});

/**
 * Action creator for setting transactions data
 * @param {Array} transactions - Transactions array
 */
export const setTransactions = (transactions) => ({
  type: 'SET_TRANSACTIONS',
  payload: transactions
});

/**
 * Action creator for showing notification
 * @param {Object} notification - Notification data
 * @param {string} notification.type - Notification type (success, error, warning, info)
 * @param {string} notification.message - Notification message
 * @param {number} notification.duration - Auto-dismiss duration in ms
 */
export const showNotification = (notification) => ({
  type: 'SHOW_NOTIFICATION',
  payload: {
    id: Date.now(),
    duration: 5000,
    ...notification
  }
});

/**
 * Action creator for hiding notification
 * @param {number} notificationId - Notification ID to hide
 */
export const hideNotification = (notificationId) => ({
  type: 'HIDE_NOTIFICATION',
  payload: notificationId
});

// ============================================================================
// ERROR HANDLING MIDDLEWARE HELPERS
// ============================================================================

/**
 * Generic error handler for rejected async thunks
 * @param {Object} action - Redux action
 * @param {Function} dispatch - Redux dispatch function
 */
export const handleAsyncError = (action, dispatch) => {
  const errorMessage = action.payload || 'An unexpected error occurred';

  // Show error notification
  dispatch(showNotification({
    type: 'error',
    message: errorMessage,
    duration: 8000
  }));

  // Log error for debugging
  console.error(`Action ${action.type} failed:`, errorMessage);

  // Handle specific error types
  if (errorMessage.includes('unauthorized') || errorMessage.includes('401')) {
    // Token might be expired, try to refresh
    dispatch(refreshToken());
  }
};

/**
 * Success handler for completed async thunks
 * @param {Object} action - Redux action
 * @param {Function} dispatch - Redux dispatch function
 */
export const handleAsyncSuccess = (action, dispatch) => {
  // Show success notification for certain actions
  const successActions = [
    'auth/loginUser/fulfilled',
    'auth/registerUser/fulfilled',
    'finance/processPayment/fulfilled',
    'finance/applyForFinancing/fulfilled'
  ];

  if (successActions.includes(action.type)) {
    let message = 'Operation completed successfully';

    if (action.type.includes('loginUser')) {
      message = 'Welcome back! Login successful';
    } else if (action.type.includes('registerUser')) {
      message = 'Account created successfully';
    } else if (action.type.includes('processPayment')) {
      message = 'Payment processed successfully';
    } else if (action.type.includes('applyForFinancing')) {
      message = 'Financing application submitted successfully';
    }

    dispatch(showNotification({
      type: 'success',
      message,
      duration: 4000
    }));
  }
};

export default {
  // Auth actions
  loginUser,
  registerUser,
  logoutUser,
  refreshToken,
  fetchUserProfile,

  // Analytics actions
  fetchDashboardAnalytics,
  fetchRevenueAnalytics,
  fetchCustomerAnalytics,
  fetchTransactionAnalytics,
  fetchAIInsights,
  updateAnalyticsFilters,

  // Finance actions
  fetchPaymentMethods,
  processPayment,
  fetchTransactionHistory,
  fetchFinancingOptions,
  applyForFinancing,
  fetchFinancingApplications,
  syncPaymentData,
  fetchAccountBalance,

  // AI actions
  sendAIMessage,
  fetchAIChatHistory,

  // Utility actions
  initializeApp,
  clearErrors,
  setGlobalLoading,
  setLoading,
  setPayments,
  setTransactions,
  showNotification,
  hideNotification,

  // Error handling
  handleAsyncError,
  handleAsyncSuccess
};