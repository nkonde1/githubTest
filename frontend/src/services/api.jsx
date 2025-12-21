import axios from 'axios';

/**
 * Centralized API service with authentication, interceptors, and error handling
 * Provides consistent HTTP client configuration for the entire application
 */

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_APP_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Prevent duplicate interceptors in HMR by tracking attachment
if (!window.__EFP_api_interceptors_attached) {
  window.__EFP_api_interceptors_attached = { requestId: null, responseId: null };
}

// Request interceptor for authentication
const requestInterceptorId = apiClient.interceptors.request.use(
  (config) => {
    // Add auth token to requests
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request ID for tracking
    config.headers['X-Request-ID'] = generateRequestId();

    // Log request in development
    if (import.meta.env.NODE_ENV === 'development') {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
        data: config.data,
        params: config.params,
      });
    }

    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
const responseInterceptorId = apiClient.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.NODE_ENV === 'development') {
      console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data,
      });
    }

    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized - token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // Clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle different error types
    const errorMessage = getErrorMessage(error);
    
    // Log error in development
    if (import.meta.env.NODE_ENV === 'development') {
      console.error(`❌ API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
        status: error.response?.status,
        message: errorMessage,
        data: error.response?.data,
      });
    }

    // Enhance error object
    error.message = errorMessage;
    return Promise.reject(error);
  }
);

// Save interceptor IDs and clean up on HMR
window.__EFP_api_interceptors_attached.requestId = requestInterceptorId;
window.__EFP_api_interceptors_attached.responseId = responseInterceptorId;

try {
  if (import.meta && import.meta.hot) {
    import.meta.hot.dispose(() => {
      const ids = window.__EFP_api_interceptors_attached;
      if (ids?.requestId !== null) {
        apiClient.interceptors.request.eject(ids.requestId);
        ids.requestId = null;
      }
      if (ids?.responseId !== null) {
        apiClient.interceptors.response.eject(ids.responseId);
        ids.responseId = null;
      }
    });
  } else if (typeof module !== 'undefined' && module.hot) {
    module.hot.dispose(() => {
      const ids = window.__EFP_api_interceptors_attached;
      if (ids?.requestId !== null) {
        apiClient.interceptors.request.eject(ids.requestId);
        ids.requestId = null;
      }
      if (ids?.responseId !== null) {
        apiClient.interceptors.response.eject(ids.responseId);
        ids.responseId = null;
      }
    });
  }
} catch (_) {
  // no-op
}

/**
 * Generate unique request ID for tracking
 * @returns {string} Unique request ID
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Extract user-friendly error message from error response
 * @param {Object} error - Axios error object
 * @returns {string} User-friendly error message
 */
function getErrorMessage(error) {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    if (data?.message) {
      return data.message;
    }
    
    if (data?.detail) {
      return Array.isArray(data.detail) ? data.detail[0]?.msg || 'Validation error' : data.detail;
    }
    
    // Default messages for common status codes
    switch (status) {
      case 400:
        return 'Bad request. Please check your input.';
      case 401:
        return 'Authentication required. Please log in.';
      case 403:
        return 'Access denied. You don\'t have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return 'Conflict. The resource already exists or is in use.';
      case 422:
        return 'Validation error. Please check your input.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Internal server error. Please try again later.';
      case 502:
        return 'Service temporarily unavailable. Please try again later.';
      case 503:
        return 'Service unavailable. Please try again later.';
      default:
        return `Server error (${status}). Please try again later.`;
    }
  } else if (error.request) {
    // Network error
    return 'Network error. Please check your internet connection.';
  } else {
    // Other error
    return error.message || 'An unexpected error occurred.';
  }
}

let authToken = '';

export const setAuthToken = (token) => {
  authToken = token;
  // Set the token in Axios default headers or wherever necessary
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

/**
 * API service methods for common operations
 */
export const apiService = {
  // Generic HTTP methods
  get: (url, config = {}) => apiClient.get(url, config),
  post: (url, data = {}, config = {}) => apiClient.post(url, data, config),
  put: (url, data = {}, config = {}) => apiClient.put(url, data, config),
  patch: (url, data = {}, config = {}) => apiClient.patch(url, data, config),
  delete: (url, config = {}) => apiClient.delete(url, config),

  // File upload
  uploadFile: (url, file, onProgress = null) => {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress ? (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      } : undefined,
    });
  },

  // Download file
  downloadFile: async (url, filename) => {
    try {
      const response = await apiClient.get(url, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      return response;
    } catch (error) {
      console.error('File download error:', error);
      throw error;
    }
  },

  // Health check
  healthCheck: () => apiClient.get('/health'),

  // Cancel request
  cancelRequest: (cancelToken) => {
    if (cancelToken) {
      cancelToken.cancel('Request canceled by user');
    }
  },

  // Create cancel token
  createCancelToken: () => axios.CancelToken.source(),
};

// Export axios instance for direct use
export { apiClient };

export const api = apiClient; // Add this line

// Export default
export default apiService;