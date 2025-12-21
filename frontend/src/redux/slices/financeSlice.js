

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../services/api';

/**
 * Finance and lending management slice
 * Handles financing offers, loan applications, and credit assessments
 *
 * Optimized for memory efficiency by encouraging pagination and specific resets.
 */

// Async thunks for finance API calls
export const fetchFinancingOffers = createAsyncThunk(
  'finance/fetchOffers',
  async ({ businessId }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/financing/offers?business_id=${businessId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch offers');
    }
  }
);

export const submitLoanApplication = createAsyncThunk(
  'finance/submitApplication',
  async (applicationData, { rejectWithValue }) => {
    try {
      const response = await api.post('/financing/applications', applicationData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to submit application');
    }
  }
);

export const fetchCreditAssessment = createAsyncThunk(
  'finance/fetchCreditAssessment',
  async ({ businessId }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/financing/credit-assessment/${businessId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch credit assessment');
    }
  }
);

export const fetchLoanApplications = createAsyncThunk(
  'finance/fetchApplications',
  // Ensure the API respects these limit/page parameters
  async ({ status = 'all', page = 1, limit = 20 }, { rejectWithValue }) => {
    try {
      const response = await api.get('/financing/applications', {
        params: { status, page, limit }
      });
      return response.data; // Expecting { applications: [...], totalCount: N }
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch applications');
    }
  }
);

export const fetchRepaymentSchedule = createAsyncThunk(
  'finance/fetchRepaymentSchedule',
  async ({ loanId }, { rejectWithValue }) => {
    try {
      const response = await api.get(`/financing/loans/${loanId}/schedule`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch repayment schedule');
    }
  }
);

export const makeRepayment = createAsyncThunk(
  'finance/makeRepayment',
  async ({ loanId, amount, paymentMethod }, { rejectWithValue }) => {
    try {
      const response = await api.post(`/financing/loans/${loanId}/repay`, {
        amount,
        payment_method: paymentMethod
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Payment failed');
    }
  }
);

// --- New Async Thunk for Paginated Payment History ---
export const fetchPaymentHistory = createAsyncThunk(
  'finance/fetchPaymentHistory',
  async ({ page = 1, limit = 20, filters = {} }, { rejectWithValue }) => {
    try {
      // Map filters to query params
      const params = {
        page,
        limit,
        status: filters.status,
        search: filters.search
      };

      const response = await api.get('/api/v1/payments/transactions', { params });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch payment history');
    }
  }
);
// --- End New Async Thunk ---

export const addTransaction = createAsyncThunk(
  'finance/addTransaction',
  async (transactionData, { rejectWithValue, dispatch }) => {
    try {
      const response = await api.post('/api/v1/payments/transactions', transactionData);
      // Refresh the list to show the new transaction
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

  creditAssessment: {
    score: null,
    factors: [],
    recommendations: [],
    riskLevel: null,
    loading: false,
    error: null
  },

  // Loan applications - `list` needs careful management
  applications: {
    list: [],
    totalApplicationsCount: 0, // Added for pagination
    current: null,
    loading: false,
    error: null,
    submitting: false
  },

  // Active loans - `list` needs careful management
  activeLoans: {
    list: [],
    totalOutstanding: 0,
    nextPayment: null,
    loading: false,
    error: null
  },

  // Repayment schedule - `schedule` can be long, but usually for one loan at a time
  repaymentSchedule: {
    schedule: [],
    totalPaid: 0,
    remainingBalance: 0,
    loading: false,
    error: null
  },

  // Payment history - THIS IS THE BIG ONE FOR POTENTIAL MEMORY ISSUES
  paymentHistory: {
    payments: [], // This will be your paginated 'transactions'
    totalPaymentsCount: 0, // Added for pagination
    loading: false,
    error: null
  },

  // Aggregated payment stats (generally small)
  paymentStats: {
    total_revenue: 0,
    transaction_count: 0,
    avg_transaction_value: 0,
    success_rate: 0,
    revenue_growth: 0,
    dispute_rate: 0,
    payment_method_distribution: {},
    daily_revenue: [], // Could be large if not aggregated
    loading: false,
    error: null,
    lastFetched: null,
  },

  settings: {
    autoRepayment: false,
    notificationPreferences: {
      paymentReminders: true,
      offerAlerts: true,
      statusUpdates: true
    },
    preferredRepaymentMethod: 'bank_transfer'
  }
};

// Finance slice
const financeSlice = createSlice({
  name: 'finance',
  initialState,
  reducers: {
    // Settings actions
    updateFinanceSettings: (state, action) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    updateNotificationPreferences: (state, action) => {
      state.settings.notificationPreferences = {
        ...state.settings.notificationPreferences,
        ...action.payload
      };
    },

    // Application actions
    updateCurrentApplication: (state, action) => {
      state.applications.current = { ...state.applications.current, ...action.payload };
    },
    clearCurrentApplication: (state) => {
      state.applications.current = null;
    },

    // Clear errors
    clearFinanceErrors: (state) => {
      state.offers.error = null;
      state.creditAssessment.error = null;
      state.applications.error = null;
      state.activeLoans.error = null;
      state.repaymentSchedule.error = null;
      state.paymentHistory.error = null;
      state.paymentStats.error = null;
    },

    // Reset finance state
    resetFinanceState: () => initialState,
    // Specific reset for loan applications list
    resetLoanApplications: (state) => {
      state.applications.list = initialState.applications.list;
      state.applications.totalApplicationsCount = initialState.applications.totalApplicationsCount;
    },
    // Specific reset for active loans list
    resetActiveLoans: (state) => {
      state.activeLoans.list = initialState.activeLoans.list;
    },
    // Specific reset for payment history
    resetPaymentHistory: (state) => {
      state.paymentHistory = initialState.paymentHistory;
    },
    // Specific reset for a single repayment schedule (on loan change, etc.)
    resetRepaymentSchedule: (state) => {
      state.repaymentSchedule = initialState.repaymentSchedule;
    },
    // Specific reset for payment stats if needed (often aggregated, so less critical)
    resetPaymentStats: (state) => {
      state.paymentStats = initialState.paymentStats;
    }
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
        state.offers.available = action.payload.offers || [];
        state.offers.recommended = action.payload.recommended || [];
        state.offers.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchFinancingOffers.rejected, (state, action) => {
        state.offers.loading = false;
        state.offers.error = action.payload;
      })

      // Credit assessment cases
      .addCase(fetchCreditAssessment.pending, (state) => {
        state.creditAssessment.loading = true;
        state.creditAssessment.error = null;
      })
      .addCase(fetchCreditAssessment.fulfilled, (state, action) => {
        state.creditAssessment.loading = false;
        state.creditAssessment = { ...state.creditAssessment, ...action.payload };
      })
      .addCase(fetchCreditAssessment.rejected, (state, action) => {
        state.creditAssessment.loading = false;
        state.creditAssessment.error = action.payload;
      })

      // Loan application submission cases
      .addCase(submitLoanApplication.pending, (state) => {
        state.applications.submitting = true;
        state.applications.error = null;
      })
      .addCase(submitLoanApplication.fulfilled, (state, action) => {
        state.applications.submitting = false;
        // Prepend new application, but consider total size limits or server-side refresh
        state.applications.list.unshift(action.payload);
        state.applications.current = null;
        state.applications.totalApplicationsCount++; // Increment count
      })
      .addCase(submitLoanApplication.rejected, (state, action) => {
        state.applications.submitting = false;
        state.applications.error = action.payload;
      })

      // Fetch applications cases - replace list on fetch (for pagination)
      .addCase(fetchLoanApplications.pending, (state) => {
        state.applications.loading = true;
        state.applications.error = null;
      })
      .addCase(fetchLoanApplications.fulfilled, (state, action) => {
        state.applications.loading = false;
        // IMPORTANT: Replace the list on new fetch to avoid accumulation
        state.applications.list = action.payload.applications || [];
        state.applications.totalApplicationsCount = action.payload.totalCount ?? 0;
        state.applications.error = null;
      })
      .addCase(fetchLoanApplications.rejected, (state, action) => {
        state.applications.loading = false;
        state.applications.error = action.payload;
      })

      // Repayment schedule cases - always replace the schedule
      .addCase(fetchRepaymentSchedule.pending, (state) => {
        state.repaymentSchedule.loading = true;
        state.repaymentSchedule.error = null;
      })
      .addCase(fetchRepaymentSchedule.fulfilled, (state, action) => {
        state.repaymentSchedule.loading = false;
        // Always replace the schedule for the current loan
        state.repaymentSchedule.schedule = action.payload.schedule || [];
        state.repaymentSchedule.totalPaid = action.payload.totalPaid ?? 0;
        state.repaymentSchedule.remainingBalance = action.payload.remainingBalance ?? 0;
        state.repaymentSchedule.error = null;
      })
      .addCase(fetchRepaymentSchedule.rejected, (state, action) => {
        state.repaymentSchedule.loading = false;
        state.repaymentSchedule.error = action.payload;
      })

      // Make repayment cases (updates existing payment history and potentially active loans)
      .addCase(makeRepayment.pending, (state) => {
        state.paymentHistory.loading = true;
        state.paymentHistory.error = null;
      })
      .addCase(makeRepayment.fulfilled, (state, action) => {
        state.paymentHistory.loading = false;
        // Prepend the new payment to the *current page* of payment history.
        // This assumes that the payment history component would refetch
        // or update its view to ensure the new payment is correctly positioned
        // within the paginated list.
        state.paymentHistory.payments.unshift(action.payload);
        state.paymentHistory.totalPaymentsCount++; // Increment count
        // Update remaining balance if the repayment is for an active loan
        if (state.repaymentSchedule.remainingBalance !== null) {
          state.repaymentSchedule.remainingBalance -= action.payload.amount;
        }
        state.paymentHistory.error = null;
      })
      .addCase(makeRepayment.rejected, (state, action) => {
        state.paymentHistory.loading = false;
        state.paymentHistory.error = action.payload;
      })

      // --- New extraReducers for fetchPaymentHistory ---
      .addCase(fetchPaymentHistory.pending, (state) => {
        state.paymentHistory.loading = true;
        state.paymentHistory.error = null;
      })
      .addCase(fetchPaymentHistory.fulfilled, (state, action) => {
        state.paymentHistory.loading = false;
        console.log('fetchPaymentHistory payload:', action.payload); // DEBUG
        // Replace the current page of payment history
        // FIXED: Backend (routes/payments.py) returns 'items' and 'total'
        state.paymentHistory.payments = action.payload.items || [];
        state.paymentHistory.totalPaymentsCount = action.payload.total ?? 0;
        state.paymentHistory.error = null;
      })
      .addCase(fetchPaymentHistory.rejected, (state, action) => {
        state.paymentHistory.loading = false;
        state.paymentHistory.error = action.payload;
      })
      // --- End New extraReducers for fetchPaymentHistory ---

      // --- extraReducers for fetchPaymentStats ---
      .addCase(fetchPaymentStats.pending, (state) => {
        state.paymentStats.loading = true;
        state.paymentStats.error = null;
      })
      .addCase(fetchPaymentStats.fulfilled, (state, action) => {
        state.paymentStats.loading = false;

        // Currency Conversion Logic (Target: ZMW)
        const ratesToZMW = {
          'USD': 27.0,
          'EUR': 28.0,
          'ZMW': 1.00,
          'GBP': 34.0,
          'CAD': 19.0
        };

        const totalsByCurrency = action.payload.totals_by_currency || {};
        let totalRevenueZMW = 0;

        Object.entries(totalsByCurrency).forEach(([currency, amount]) => {
          const rate = ratesToZMW[currency] || 27.0; // Default to USD rate if unknown
          totalRevenueZMW += amount * rate;
        });

        // Replace aggregated stats
        state.paymentStats = {
          ...state.paymentStats,
          ...action.payload,
          // FIXED: Map backend 'total_count' to frontend 'transaction_count'
          transaction_count: action.payload.total_count ?? state.paymentStats.transaction_count,
          // FIXED: Use calculated ZMW total
          total_revenue: totalRevenueZMW,
          daily_revenue: action.payload.daily_revenue || [],
          lastFetched: new Date().toISOString()
        };
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
  updateFinanceSettings,
  updateNotificationPreferences,
  updateCurrentApplication,
  clearCurrentApplication,
  clearFinanceErrors,
  resetFinanceState,
  resetLoanApplications,
  resetActiveLoans,
  resetPaymentHistory,
  resetRepaymentSchedule,
  resetPaymentStats
} = financeSlice.actions;

// Selectors
export const selectFinancingOffers = (state) => state.finance.offers;
export const selectCreditAssessment = (state) => state.finance.creditAssessment;
export const selectLoanApplications = (state) => state.finance.applications;
export const selectActiveLoans = (state) => state.finance.activeLoans;
export const selectRepaymentSchedule = (state) => state.finance.repaymentSchedule;
export const selectPaymentHistory = (state) => state.finance.paymentHistory;
export const selectFinanceSettings = (state) => state.finance.settings;

// --- NEW SELECTORS FOR PAYMENT HUB (FIXED: now properly exported) ---
export const selectPaymentStats = (state) => state.finance.paymentStats;
export const selectPaymentLoading = (state) => state.finance.paymentStats.loading;
export const selectPaymentError = (state) => state.finance.paymentStats.error;
export const selectTransactions = (state) => state.finance.paymentHistory.payments; // This was already here, keeping for completeness
// --- END NEW SELECTORS ---

export default financeSlice.reducer;