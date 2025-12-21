import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: false  // Set to true if using cookies, false for Bearer tokens
});

// Add request interceptor to attach token
apiClient.interceptors.request.use(
  (config) => {
    // FIXED: Try multiple sources for token to ensure we get it
    let token = localStorage.getItem('access_token') || localStorage.getItem('token');
    
    // If not in localStorage, try to get from Redux via the API module
    if (!token && typeof window !== 'undefined' && window.__REDUX_STORE__) {
      const state = window.__REDUX_STORE__.getState();
      token = state.user?.token;
    }
    
    console.log('📤 Request to:', config.url);
    console.log('Token present:', !!token);
    console.log('Token source:', token ? (localStorage.getItem('access_token') ? 'localStorage' : 'Redux') : 'none');
    
    if (token) {
      // Make sure token is attached to Authorization header
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ Authorization header set');
      console.log('Header value:', config.headers.Authorization.substring(0, 50) + '...');
    } else {
      console.warn('⚠️ No token found in localStorage or Redux');
    }
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('❌ Response error:', error.response?.status, error.response?.data);
    
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.error('Authentication failed. Checking token...');
      const token = localStorage.getItem('token');
      console.log('Token exists:', !!token);
      if (token) {
        console.log('Token format:', token.split('.').length === 3 ? '✅ Valid (3 parts)' : '❌ Invalid');
      }
    }
    
    return Promise.reject(error);
  }
);

export const getAnalytics = async (timeframe = '30d') => {
  try {
    console.log('📊 Fetching analytics with timeframe:', timeframe);
    
    const response = await apiClient.get('/api/v1/analytics/', {
      params: { timeframe }
    });
    
    console.log('✅ Analytics data received:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error fetching analytics:', {
      status: error.response?.status,
      message: error.response?.data?.message || error.message,
      data: error.response?.data
    });
    throw error;
  }
};

export const getCustomerAnalytics = async (timeframe = '30d') => {
  try {
    console.log('📊 Fetching customer analytics with timeframe:', timeframe);
    
    const response = await apiClient.get('/api/v1/analytics/customers/insights', {
      params: { timeframe }
    });
    
    console.log('✅ Customer analytics data received:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error fetching customer analytics:', {
      status: error.response?.status,
      message: error.response?.data?.message || error.message,
      data: error.response?.data
    });
    throw error;
  }
};

export const debugAuth = () => {
  console.log('\n🔍 === AUTHENTICATION DEBUG ===');
  const token = localStorage.getItem('token');
  
  if (!token) {
    console.error('❌ NO TOKEN FOUND - User is not logged in');
  } else {
    console.log('✅ Token found in localStorage');
    console.log('   Length:', token.length);
    
    const parts = token.split('.');
    console.log('   Parts:', parts.length, parts.length === 3 ? '✅ (valid JWT)' : '❌ (invalid JWT)');
    
    if (parts.length === 3) {
      try {
        // Decode and log payload (header.payload.signature)
        const payload = JSON.parse(atob(parts[1]));
        console.log('   Payload:', payload);
        console.log('   User ID (sub):', payload.sub);
        console.log('   Expires (exp):', new Date(payload.exp * 1000).toISOString());
      } catch (e) {
        console.error('   Could not decode payload:', e.message);
      }
    }
  }
  
  console.log('🔍 === END DEBUG ===\n');
};

// Call this on app initialization to verify auth
export const verifyAuth = async () => {
  debugAuth();
  
  const token = localStorage.getItem('token');
  if (!token) {
    console.warn('⚠️ No token - user needs to log in');
    return false;
  }
  
  try {
    // Try a simple request to verify token is valid
    const response = await apiClient.get('/api/v1/auth/me');
    console.log('✅ Auth verified - user:', response.data.email);
    return true;
  } catch (error) {
    console.error('❌ Auth verification failed:', error.response?.data?.message);
    return false;
  }
};