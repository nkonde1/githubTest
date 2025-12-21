// src/redux/store.js (changed from .jsx to .js)
import { configureStore } from '@reduxjs/toolkit';

// Import reducers - change extensions from .jsx to .js
import userReducer from './slices/user_slice.js';
import financeReducer from './slices/financeSlice.js';
import analyticsReducer from './slices/analyticsSlice.js';
import authReducer from './slices/authSlice.js';
import metricsReducer from './slices/metricsSlice';
import aiChatReducer from './slices/aiChatSlice.js';

// Dashboard Reducer - Consider converting to RTK slice
const initialDashboardState = {
  metrics: {},
  loading: false,
  error: null,
  lastUpdated: null,
};

const dashboardReducer = (state = initialDashboardState, action) => {
  switch (action.type) {
    case 'SET_DASHBOARD_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    case 'SET_DASHBOARD_METRICS':
      return {
        ...state,
        metrics: action.payload,
        loading: false,
        error: null,
        lastUpdated: new Date().toISOString(),
      };
    case 'SET_DASHBOARD_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    case 'UPDATE_METRIC':
      return {
        ...state,
        metrics: {
          ...state.metrics,
          [action.payload.key]: action.payload.value,
        },
      };
    case 'RESET_DASHBOARD': // Add reset action
      return initialDashboardState;
    default:
      return state;
  }
};

// Payment Reducer
const initialPaymentState = {
  payments: {},
  connectedProviders: [],
  loading: false,
  error: null,
};

const paymentReducer = (state = initialPaymentState, action) => {
  switch (action.type) {
    case 'SET_PAYMENT_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    case 'SET_PAYMENTS':
      return {
        ...state,
        payments: action.payload,
        loading: false,
        error: null,
      };
    case 'SET_CONNECTED_PROVIDERS':
      return {
        ...state,
        connectedProviders: action.payload,
      };
    case 'ADD_PAYMENT_PROVIDER':
      return {
        ...state,
        connectedProviders: [...state.connectedProviders, action.payload],
      };
    case 'REMOVE_PAYMENT_PROVIDER':
      return {
        ...state,
        connectedProviders: state.connectedProviders.filter(
          provider => provider !== action.payload
        ),
      };
    case 'SET_PAYMENT_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    case 'RESET_PAYMENTS': // Add reset action
      return initialPaymentState;
    default:
      return state;
  }
};

// Financing Reducer
const initialFinancingState = {
  offers: [],
  activeFinancing: [],
  applications: [],
  loading: false,
  error: null,
};

const financingReducer = (state = initialFinancingState, action) => {
  switch (action.type) {
    case 'SET_FINANCING_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_FINANCING_OFFERS':
      return { ...state, offers: action.payload, loading: false };
    case 'SET_FINANCING_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'RESET_FINANCING': // Add reset action
      return initialFinancingState;
    default:
      return state;
  }
};

// UI Reducer with notification cleanup
const MAX_NOTIFICATIONS = 10; // Prevent unlimited growth

const initialUIState = {
  sidebarOpen: true,
  notifications: []
};

const uiReducer = (state = initialUIState, action) => {
  switch (action.type) {
    case 'TOGGLE_SIDEBAR':
      return {
        ...state,
        sidebarOpen: !state.sidebarOpen,
      };
    case 'SET_SIDEBAR':
      return {
        ...state,
        sidebarOpen: action.payload,
      };
    case 'ADD_NOTIFICATION':
      const newNotifications = [...state.notifications, action.payload];
      // Keep only the most recent notifications to prevent memory bloat
      return {
        ...state,
        notifications: newNotifications.length > MAX_NOTIFICATIONS 
          ? newNotifications.slice(-MAX_NOTIFICATIONS) 
          : newNotifications,
      };
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(
          notification => notification.id !== action.payload
        ),
      };
    case 'CLEAR_NOTIFICATIONS':
      return {
        ...state,
        notifications: [],
      };
    case 'RESET_UI': // Add reset action
      return initialUIState;
    default:
      return state;
  }
};

export const store = configureStore({
  reducer: {
    user: userReducer,
    metrics: metricsReducer,
    finance: financeReducer,
    analytics: analyticsReducer,
    auth: authReducer,
    dashboard: dashboardReducer,
    payments: paymentReducer,
    financing: financingReducer,
    ui: uiReducer,
    aiChat: aiChatReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types for serialization checks
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export default store;
