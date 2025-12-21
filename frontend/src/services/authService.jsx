import api, { setAuthToken } from './api'; // top-level import of configured Axios instance
import axios from 'axios';
const API_URL = import.meta.env.VITE_APP_API_URL || 'http://localhost:8000';

class AuthService {
  constructor() {
    this.tokenKey = 'access_token';
    this.refreshTokenKey = 'refresh_token';
    this.userKey = 'finance_user';

    // FIXED: Add refresh timer tracking for cleanup
    this.refreshTimer = null;
    this.isRefreshing = false;

    // FIXED: Add request interceptor to handle token refresh automatically
    this.setupInterceptors();
  }

  /**
   * FIXED: Setup Axios interceptors for automatic token handling
   */
  setupInterceptors() {
    // Avoid duplicate interceptors if central API already handles refresh logic
    try {
      if (window.__EFP_api_interceptors_attached && window.__EFP_api_interceptors_attached.responseId != null) {
        return;
      }
    } catch (_) {
      // no-op
    }
    // Response interceptor to handle 401 errors and auto-refresh
    try {
      if (api && api.interceptors && typeof api.interceptors.response?.use === 'function') {
        api.interceptors.response.use(
          (response) => response,
          async (error) => {
            const originalRequest = error?.config || {};

            // Defensive checks: ensure headers object exists before reading/writing
            originalRequest.headers = originalRequest.headers || {};

            if (error.response?.status === 401 && !originalRequest._retry) {
              originalRequest._retry = true;

              try {
                await this.refreshToken();
                // Retry the original request with new token
                const token = this.getAccessToken();
                if (token) {
                  originalRequest.headers['Authorization'] = `Bearer ${token}`;
                  return api(originalRequest);
                }
              } catch (refreshError) {
                this.clearTokens();
                // Redirect to login or dispatch logout action
                return Promise.reject(refreshError);
              }
            }

            return Promise.reject(error);
          }
        );
      } else {
        console.warn('AuthService: api.interceptors not available, skipping interceptor setup.');
      }
    } catch (e) {
      console.error('AuthService: Failed to attach interceptors', e);
    }
  }

  /**
   * Helper to set tokens in localStorage and update Axios default headers.
   */
  setTokens(accessToken, refreshToken) {
    if (!accessToken) return;

    localStorage.setItem(this.tokenKey, accessToken);
    if (refreshToken) {
      localStorage.setItem(this.refreshTokenKey, refreshToken);
    }
    if (api && api.defaults && api.defaults.headers && api.defaults.headers.common) {
      api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    }

    // Keep central API helper in sync if provided
    if (typeof setAuthToken === 'function') {
      try { setAuthToken(accessToken); } catch (_) { /* no-op */ }
    }

    // FIXED: Setup new refresh timer when tokens are set
    this.setupTokenRefresh();

    if (process.env.NODE_ENV === 'development') {
      console.log('AuthService: Tokens set in localStorage and Axios headers.');
    }
  }

  /**
   * Helper to clear tokens from localStorage and remove Axios default headers.
   */
  clearTokens() {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
    if (api && api.defaults && api.defaults.headers && api.defaults.headers.common) {
      delete api.defaults.headers.common['Authorization'];
    }
    if (typeof setAuthToken === 'function') {
      try { setAuthToken(null); } catch (_) { /* no-op */ }
    }

    // FIXED: Clear refresh timer to prevent memory leaks
    this.clearRefreshTimer();

    if (process.env.NODE_ENV === 'development') {
      console.log('AuthService: Tokens cleared from localStorage and Axios headers.');
    }
  }

  /**
   * FIXED: Clear refresh timer safely
   */
  clearRefreshTimer() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  getAccessToken() {
    return localStorage.getItem(this.tokenKey);
  }

  getRefreshToken() {
    return localStorage.getItem(this.refreshTokenKey);
  }

  getStoredUser() {
    try {
      const userData = localStorage.getItem(this.userKey);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('AuthService: Error parsing stored user data:', error);
      localStorage.removeItem(this.userKey);
      return null;
    }
  }

  // --- Core Authentication Methods ---

  async login(email, password) {
    try {
      const response = await api.post('/api/v1/auth/login-json', { email, password });
      const responseData = response.data;

      const {
        access_token,
        refresh_token,
        token_type,
        ...userData
      } = responseData;

      if (access_token) {
        this.setTokens(access_token, refresh_token);
        // FIXED: Safely store user data
        try {
          localStorage.setItem(this.userKey, JSON.stringify(userData));
        } catch (storageError) {
          console.warn('AuthService: Failed to store user data:', storageError);
        }
      }

      return {
        user: userData,
        token: access_token,
        refresh_token: refresh_token,
        ...responseData
      };
    } catch (error) {
      console.error('AuthService: Login error:', error);
      this.clearTokens();

      if (error.code === 'ERR_NETWORK') {
        throw new Error('Network error. Please check your internet connection and try again.');
      } else if (error.response?.status === 401) {
        throw new Error('Invalid email or password.');
      } else if (error.response?.status === 500) {
        throw new Error('Server error. Please try again later.');
      } else {
        throw new Error(error.response?.data?.message || 'Login failed. Please try again.');
      }
    }
  }

  async register(userData) {
    try {
      const response = await api.post('/api/v1/auth/register', userData);
      const responseData = response.data;

      const {
        access_token,
        refresh_token,
        token_type,
        ...registeredUserData
      } = responseData;

      if (access_token) {
        this.setTokens(access_token, refresh_token);
        try {
          localStorage.setItem(this.userKey, JSON.stringify(registeredUserData));
        } catch (storageError) {
          console.warn('AuthService: Failed to store user data:', storageError);
        }
      }

      return {
        user: registeredUserData,
        token: access_token,
        refresh_token: refresh_token,
        ...responseData
      };
    } catch (error) {
      console.error('AuthService: Registration error:', error);
      this.clearTokens();

      if (error.response?.status === 400) {
        throw new Error(error.response?.data?.message || 'Registration failed. Please check your information.');
      } else if (error.response?.status === 409) {
        throw new Error('Email already exists. Please use a different email.');
      } else {
        throw new Error(error.response?.data?.message || 'Registration failed. Please try again.');
      }
    }
  }

  async logout() {
    try {
      const refreshToken = this.getRefreshToken();
      if (refreshToken) {
        await api.post('/api/v1/auth/logout', { refresh_token: refreshToken });
        if (process.env.NODE_ENV === 'development') {
          console.log('AuthService: Backend logout successful.');
        }
      }
    } catch (error) {
      console.warn('AuthService: Logout endpoint error:', error.response?.data || error.message);
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser() {
    const token = this.getAccessToken();
    if (!token) {
      if (process.env.NODE_ENV === 'development') {
        console.log('AuthService: getCurrentUser - No access token found.');
      }
      this.clearTokens();
      throw new Error('No access token available');
    }

    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    try {
      const response = await api.get('/api/v1/auth/me');
      const userData = response.data;

      try {
        localStorage.setItem(this.userKey, JSON.stringify(userData));
      } catch (storageError) {
        console.warn('AuthService: Failed to store user data:', storageError);
      }

      return {
        user: userData,
        token: token
      };
    } catch (error) {
      console.error('AuthService: Get current user error:', error.response?.data || error.message);
      this.clearTokens();
      throw new Error('Failed to get current user');
    }
  }

  async updateProfile(profileData) {
    try {
      const response = await api.put('/api/v1/auth/profile', profileData);
      const userData = response.data;

      try {
        localStorage.setItem(this.userKey, JSON.stringify(userData));
      } catch (storageError) {
        console.warn('AuthService: Failed to store user data:', storageError);
      }

      return {
        user: userData
      };
    } catch (error) {
      console.error('AuthService: Profile update error:', error);
      throw new Error(error.response?.data?.message || 'Profile update failed');
    }
  }

  async changePassword(currentPassword, newPassword) {
    try {
      const response = await api.post('/api/v1/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      console.error('AuthService: Password change error:', error);
      throw new Error(error.response?.data?.message || 'Password change failed');
    }
  }

  async requestPasswordReset(email) {
    try {
      const response = await api.post('/api/v1/auth/request-reset', { email });
      return response.data;
    } catch (error) {
      console.error('AuthService: Password reset request error:', error);
      throw new Error(error.response?.data?.message || 'Password reset request failed');
    }
  }

  async resetPassword(token, newPassword) {
    try {
      const response = await api.post('/api/v1/auth/reset-password', {
        token,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      console.error('AuthService: Password reset error:', error);
      throw new Error(error.response?.data?.message || 'Password reset failed');
    }
  }

  async refreshToken() {
    // FIXED: Prevent multiple simultaneous refresh attempts
    if (this.isRefreshing) {
      return new Promise((resolve, reject) => {
        // Wait for current refresh to complete
        const checkRefresh = () => {
          if (!this.isRefreshing) {
            const token = this.getAccessToken();
            if (token) {
              resolve({ access_token: token });
            } else {
              reject(new Error('Token refresh failed'));
            }
          } else {
            setTimeout(checkRefresh, 100);
          }
        };
        checkRefresh();
      });
    }

    this.isRefreshing = true;

    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        console.error('AuthService: Refresh token missing.');
        this.clearTokens();
        throw new Error('No refresh token available');
      }

      const response = await api.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
      const { access_token, refresh_token: newRefreshToken } = response.data;

      if (access_token) {
        this.setTokens(access_token, newRefreshToken);
      }

      return response.data;
    } catch (error) {
      console.error('AuthService: Token refresh error:', error.response?.data || error.message);
      this.clearTokens();
      throw new Error('Token refresh failed');
    } finally {
      this.isRefreshing = false;
    }
  }

  async verifyEmail(token) {
    try {
      const response = await api.post('/api/v1/auth/verify-email', { token });
      return response.data;
    } catch (error) {
      console.error('AuthService: Email verification error:', error);
      throw new Error(error.response?.data?.message || 'Email verification failed');
    }
  }

  async resendEmailVerification() {
    try {
      const response = await api.post('/api/v1/auth/resend-verification');
      return response.data;
    } catch (error) {
      console.error('AuthService: Resend verification error:', error);
      throw new Error(error.response?.data?.message || 'Resend verification failed');
    }
  }

  isAuthenticated() {
    const token = this.getAccessToken();
    if (!token) return false;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp > currentTime;
    } catch (error) {
      console.error('AuthService: Token validation error:', error);
      this.clearTokens();
      return false;
    }
  }

  getUserFromToken() {
    const token = this.getAccessToken();
    if (!token) return null;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        id: payload.sub,
        email: payload.email,
        exp: payload.exp
      };
    } catch (error) {
      console.error('AuthService: Token parsing error:', error);
      return null;
    }
  }

  /**
   * FIXED: Memory-safe token refresh setup with proper cleanup
   */
  setupTokenRefresh(onTokenRefresh) {
    // Clear any existing timer first
    this.clearRefreshTimer();

    const token = this.getAccessToken();
    if (!token) return;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expirationTime = payload.exp * 1000;
      const currentTime = Date.now();

      // Refresh 5 minutes before expiration
      const refreshTime = Math.max(expirationTime - currentTime - (5 * 60 * 1000), 0);

      if (refreshTime <= 0) {
        if (process.env.NODE_ENV === 'development') {
          console.warn('AuthService: Token expired, attempting immediate refresh.');
        }
        this.refreshToken().then(() => {
          if (onTokenRefresh) onTokenRefresh();
          // FIXED: Only setup new timer after successful refresh
          this.setupTokenRefresh(onTokenRefresh);
        }).catch(err => {
          console.error('AuthService: Immediate token refresh failed:', err);
          this.clearTokens();
        });
        return;
      }

      if (process.env.NODE_ENV === 'development') {
        console.log(`AuthService: Setting up token refresh in ${Math.round(refreshTime / 1000)} seconds.`);
      }

      // FIXED: Store timer reference for cleanup and use single refresh
      this.refreshTimer = setTimeout(async () => {
        try {
          await this.refreshToken();
          if (onTokenRefresh) onTokenRefresh();
          // FIXED: Only setup new timer after successful refresh
          this.setupTokenRefresh(onTokenRefresh);
        } catch (error) {
          console.error('AuthService: Automatic token refresh failed:', error);
          this.clearTokens();
        }
      }, refreshTime);

    } catch (error) {
      console.error('AuthService: Token refresh setup error:', error);
      this.clearTokens();
    }
  }

  /**
   * FIXED: Cleanup method to call when service is no longer needed
   */
  cleanup() {
    this.clearRefreshTimer();
    this.isRefreshing = false;
  }
}

export const authService = new AuthService();

// Initialize Axios header on startup
const currentAccessToken = authService.getAccessToken();
if (currentAccessToken) {
  if (api && api.defaults && api.defaults.headers && api.defaults.headers.common) {
    api.defaults.headers.common['Authorization'] = `Bearer ${currentAccessToken}`;
  }
  if (typeof setAuthToken === 'function') {
    try { setAuthToken(currentAccessToken); } catch (_) { /* no-op */ }
  }
  if (process.env.NODE_ENV === 'development') {
    console.log('AuthService: Initial Axios header set from localStorage.');
  }
} else {
  if (api && api.defaults && api.defaults.headers && api.defaults.headers.common) {
    delete api.defaults.headers.common['Authorization'];
  }
}

// FIXED: Cleanup on page unload to prevent memory leaks (idempotent + HMR-safe)
const __EFP_auth_beforeUnloadHandler = () => {
  authService.cleanup();
};

if (!window.__EFP_auth_beforeUnloadAttached) {
  window.addEventListener('beforeunload', __EFP_auth_beforeUnloadHandler);
  window.__EFP_auth_beforeUnloadAttached = true;
}

try {
  if (import.meta && import.meta.hot) {
    import.meta.hot.dispose(() => {
      window.removeEventListener('beforeunload', __EFP_auth_beforeUnloadHandler);
      window.__EFP_auth_beforeUnloadAttached = false;
      authService.cleanup();
    });
  } else if (typeof module !== 'undefined' && module.hot) {
    module.hot.dispose(() => {
      window.removeEventListener('beforeunload', __EFP_auth_beforeUnloadHandler);
      window.__EFP_auth_beforeUnloadAttached = false;
      authService.cleanup();
    });
  }
} catch (_) {
  // no-op
}

// Convenience wrapper that uses AuthService.login (keeps single source of truth)
export const login = async (credentials) => {
  return authService.login(credentials);
};
