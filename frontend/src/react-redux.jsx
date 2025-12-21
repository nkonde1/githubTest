import { createStore, combineReducers, applyMiddleware } from 'redux';
import { thunk } from 'redux-thunk';
// Manual Redux DevTools setup
const composeWithDevTools = (typeof window !== 'undefined' && window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) || 
  ((config) => (typeof window !== 'undefined' && window.__REDUX_DEVTOOLS_EXTENSION__) ? 
    window.__REDUX_DEVTOOLS_EXTENSION__(config) : 
    (f) => f
  );

// Initial States
const initialAuthState = {
  user: null,
  isAuthenticated: false,
  loading: false,
  error: null,
};

const initialDashboardState = {
  metrics: {},
  loading: false,
  error: null,
  lastUpdated: null,
};

const initialPaymentState = {
  payments: {},
  connectedProviders: [],
  loading: false,
  error: null,
};

const initialFinancingState = {
  offers: [],
  activeFinancing: [],
  applications: [],
  loading: false,
  error: null,
};

const initialAnalyticsState = {
  profitability: {},
  customerMetrics: {},
  marketingROI: {},
  skuAnalytics: [],
  insights: [],
  loading: false,
  error: null,
};

// Auth Reducer
const authReducer = (state = initialAuthState, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        loading: false,
        error: null,
      };
    case 'SET_AUTH_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    case 'LOGOUT':
      return {
        ...initialAuthState,
      };
    default:
      return state;
  }
};

// Dashboard Reducer
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
    default:
      return state;
  }
};

// Payment Reducer
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
    default:
      return state;
  }
};

// Financing Reducer
const financingReducer = (state = initialFinancingState, action) => {
  switch (action.type) {
    case 'SET_FINANCING_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    case 'SET_FINANCING_OFFERS':
      return {
        ...state,
        offers: action.payload,
        loading: false,
        error: null,
      };
    case 'SET_ACTIVE_FINANCING':
      return {
        ...state,
        activeFinancing: action.payload,
        loading: false,
        error: null,
      };
    case 'SET_FINANCING_APPLICATIONS':
      return {
        ...state,
        applications: action.payload,
        loading: false,
        error: null,
      };
    case 'ADD_FINANCING_APPLICATION':
      return {
        ...state,
        applications: [...state.applications, action.payload],
      };
    case 'UPDATE_APPLICATION_STATUS':
      return {
        ...state,
        applications: state.applications.map(app =>
          app.id === action.payload.id
            ? { ...app, status: action.payload.status }
            : app
        ),
      };
    case 'SET_FINANCING_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    default:
      return state;
  }
};

// Analytics Reducer
const analyticsReducer = (state = initialAnalyticsState, action) => {
  switch (action.type) {
    case 'SET_ANALYTICS_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    case 'SET_PROFITABILITY_METRICS':
      return {
        ...state,
        profitability: action.payload,
        loading: false,
        error: null,
      };
    case 'SET_CUSTOMER_METRICS':
      return {
        ...state,
        customerMetrics: action.payload,
        loading: false,
        error: null,
      };
    case 'SET_MARKETING_ROI':
      return {
        ...state,
        marketingROI: action.payload,
        loading: false,
        error: null,
      };
    case 'SET_SKU_ANALYTICS':
      return {
        ...state,
        skuAnalytics: action.payload,
        loading: false,
        error: null,
      };
    case 'SET_INSIGHTS':
      return {
        ...state,
        insights: action.payload,
        loading: false,
        error: null,
      };
    case 'ADD_INSIGHT':
      return {
        ...state,
        insights: [action.payload, ...state.insights],
      };
    case 'DISMISS_INSIGHT':
      return {
        ...state,
        insights: state.insights.filter(insight => insight.id !== action.payload),
      };
    case 'SET_ANALYTICS_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    default:
      return state;
  }
};

// UI Reducer for global UI state
const uiReducer = (state = { sidebarOpen: true, notifications: [] }, action) => {
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
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
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
    default:
      return state;
  }
};

// Combine Reducers
const rootReducer = combineReducers({
  auth: authReducer,
  dashboard: dashboardReducer,
  payments: paymentReducer,
  financing: financingReducer,
  analytics: analyticsReducer,
  ui: uiReducer,
});

// Create Store
const store = createStore(
  rootReducer,
  composeWithDevTools(
    applyMiddleware(thunk)
  )
);

export default store;