// frontend/src/redux/slices/financeSlice.js

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

// Async thunks for finance API calls
export const fetchFinancingOffers = createAsyncThunk(
  'finance/fetchOffers',
  async (_, { rejectWithValue }) => { // Removed businessId as it's not used
    try {
      // FIXED: Endpoint corrected to match backend routes
      const response = await api.get('/api/v1/financing/offers');
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch offers');
    }
  }
);

export const submitLoanApplication = createAsyncThunk(
  'finance/submitApplication',
  async (applicationData, { rejectWithValue }) => {
    try {
      const response = await api.post('/api/v1/financing/applications', applicationData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to submit application');
    }
  }
);


export const fetchPaymentHistory = createAsyncThunk(
  'finance/fetchPaymentHistory',
  async ({ page = 1, limit = 20, filters = {} }, { rejectWithValue }) => {
    try {
      const params = { page, limit, status: filters.status, search: filters.search };
      const response = await api.get('/api/v1/payments/transactions', { params });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch payment history');
    }
  }
);

export const addTransaction = createAsyncThunk(
  'finance/addTransaction',
  async (transactionData, { rejectWithValue, dispatch }) => {
    try {
      const response = await api.post('/api/v1/payments/transactions', transactionData);
      dispatch(fetchPaymentHistory({ page: 1, limit: 20 }));
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to add transaction');
    }
  }
);


export const fetchPaymentStats = createAsyncThunk(
  'finance/fetchPaymentStats',
  async (filters, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/v1/payments/transactions/summary', { params: filters });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch payment statistics');
    }
  }
);

// Initial state
const initialState = {
  offers: {
    available: [],
    recommended: [],
    loading: false,
    error: null,
    lastUpdated: null
  },
  paymentHistory: {
    payments: [],
    totalPaymentsCount: 0,
    loading: false,
    error: null
  },
  paymentStats: {
    total_revenue: 0,
    transaction_count: 0,
    success_rate: 0,
    loading: false,
    error: null,
    lastFetched: null,
  },
};

// Finance slice
const financeSlice = createSlice({
  name: 'finance',
  initialState,
  reducers: {
    clearFinanceErrors: (state) => {
      state.offers.error = null;
      state.paymentHistory.error = null;
      state.paymentStats.error = null;
    },
    resetFinanceState: () => initialState,
  },

  extraReducers: (builder) => {
    builder
      // Financing offers cases
      .addCase(fetchFinancingOffers.pending, (state) => {
        state.offers.loading = true;
        state.offers.error = null;
      })
      .addCase(fetchFinancingOffers.fulfilled, (state, action) => {
        state.offers.loading = false;
        // FIXED: Correctly map the backend response to the state
        state.offers.available = action.payload.financing_options || [];
        state.offers.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchFinancingOffers.rejected, (state, action) => {
        state.offers.loading = false;
        state.offers.error = action.payload;
      })

      // Payment History cases
      .addCase(fetchPaymentHistory.pending, (state) => {
        state.paymentHistory.loading = true;
        state.paymentHistory.error = null;
      })
      .addCase(fetchPaymentHistory.fulfilled, (state, action) => {
        state.paymentHistory.loading = false;
        // FIXED: Map backend `transactions` to `payments` and `total_count` to `totalPaymentsCount`
        state.paymentHistory.payments = action.payload.transactions || [];
        state.paymentHistory.totalPaymentsCount = action.payload.total_count ?? 0;
        state.paymentHistory.error = null;
      })
      .addCase(fetchPaymentHistory.rejected, (state, action) => {
        state.paymentHistory.loading = false;
        state.paymentHistory.error = action.payload;
      })

      // Payment Stats cases
      .addCase(fetchPaymentStats.pending, (state) => {
        state.paymentStats.loading = true;
        state.paymentStats.error = null;
      })
      .addCase(fetchPaymentStats.fulfilled, (state, action) => {
        state.paymentStats.loading = false;
        // FIXED: Map backend response directly to state without currency conversion
        state.paymentStats.total_revenue = action.payload.total_revenue ?? 0;
        state.paymentStats.transaction_count = action.payload.total_transactions ?? 0;
        state.paymentStats.success_rate = action.payload.success_rate ?? 0;
        state.paymentStats.lastFetched = new Date().toISOString();
        state.paymentStats.error = null;
      })
      .addCase(fetchPaymentStats.rejected, (state, action) => {
        state.paymentStats.loading = false;
        state.paymentStats.error = action.payload;
      });
  },
});

// Export actions
export const {
  clearFinanceErrors,
  resetFinanceState,
} = financeSlice.actions;

// Selectors
export const selectFinancingOffers = (state) => state.finance.offers;
export const selectPaymentHistory = (state) => state.finance.paymentHistory;
export const selectPaymentStats = (state) => state.finance.paymentStats;
export const selectTransactions = (state) => state.finance.paymentHistory.payments;

export default financeSlice.reducer;
