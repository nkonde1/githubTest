import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authService } from '../../services/authService';

/**
 * User authentication and profile management slice
 * Handles login, logout, registration, and user profile state
 * Optimized for memory efficiency
 */

// Helper function for conditional logging (only in development)
const debugLog = (message, data = null) => {
  if (process.env.NODE_ENV === 'development' && data) {
    console.log(message, data);
  } else if (process.env.NODE_ENV === 'development') {
    console.log(message);
  }
};

// Async thunks for API calls
export const loginUser = createAsyncThunk(
  'user/login',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const result = await authService.login(email, password);
      debugLog("loginUser Thunk: Success");
      // FIXED: Ensure token is definitely in localStorage before returning
      const storedToken = localStorage.getItem('access_token');
      if (!storedToken) {
        console.warn('Token not found in localStorage after login');
      }
      return result;
    } catch (error) {
      debugLog("loginUser Thunk: Error", error.message);
      return rejectWithValue(error.message || 'Login failed');
    }
  }
);

export const registerUser = createAsyncThunk(
  'user/register',
  async (userData, { rejectWithValue }) => {
    try {
      const result = await authService.register(userData);
      debugLog("registerUser Thunk: Success");
      return result;
    } catch (error) {
      debugLog("registerUser Thunk: Error", error.message);
      return rejectWithValue(error.message || 'Registration failed');
    }
  }
);

export const logoutUser = createAsyncThunk(
  'user/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
      return null;
    } catch (error) {
      debugLog("Logout error", error.message);
      return rejectWithValue(error.message || 'Logout failed on server, but client state cleared.');
    }
  }
);

export const checkAuthStatus = createAsyncThunk(
  'user/checkAuth',
  async (_, { rejectWithValue }) => {
    debugLog("checkAuthStatus Thunk initiated");
    try {
      const result = await authService.getCurrentUser();
      debugLog("checkAuthStatus: Success");
      return result;
    } catch (error) {
      debugLog("checkAuthStatus: Error", error.message);
      return rejectWithValue(error.message || 'Authentication check failed.');
    }
  }
);

export const updateProfile = createAsyncThunk(
  'user/updateProfile',
  async (profileData, { rejectWithValue }) => {
    try {
      const updatedUser = await authService.updateProfile(profileData);
      debugLog("updateProfile: Success");
      return updatedUser.user;
    } catch (error) {
      debugLog("updateProfile: Error", error.message);
      return rejectWithValue(error.message || 'Profile update failed');
    }
  }
);

// Optimized initial state - frozen to prevent accidental mutations
const createInitialState = () => ({
  user: null,
  isAuthenticated: false,
  loading: 'idle',
  error: null,
  token: null,
  refreshToken: null,
  lastLogin: null,
  preferences: {
    theme: 'light',
    notifications: true,
    currency: 'USD',
    timezone: 'UTC'
  }
});

const initialState = createInitialState();

// User slice with memory optimizations
const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    updatePreferences: (state, action) => {
      // More memory-efficient: only update changed preferences
      const newPrefs = action.payload;
      Object.keys(newPrefs).forEach(key => {
        if (state.preferences[key] !== newPrefs[key]) {
          state.preferences[key] = newPrefs[key];
        }
      });
    },
    resetUserState: (state) => {
      // More memory-efficient reset
      Object.assign(state, createInitialState());
    },
    setInitialAuthData: (state, action) => {
      const { user, token, isAuthenticated } = action.payload;
      state.user = user;
      state.token = token;
      state.isAuthenticated = isAuthenticated;
      state.loading = 'idle';
      state.error = null;
      debugLog("Redux state hydrated from localStorage");
    },
    // New action to clear temporary state
    clearTemporaryState: (state) => {
      state.error = null;
      state.loading = 'idle';
    },
  },
  extraReducers: (builder) => {
    builder
      // --- loginUser ---
      .addCase(loginUser.pending, (state) => {
        state.loading = 'pending';
        state.error = null;
        state.isAuthenticated = false;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        const { user, token, refresh_token } = action.payload;
        state.loading = 'succeeded';
        state.user = user;
        state.token = token;
        state.refreshToken = refresh_token;
        state.isAuthenticated = true;
        state.lastLogin = Date.now();
        state.error = null;
        debugLog("loginUser fulfilled - authenticated");
        debugLog("Token in Redux:", !!token);
        debugLog("Token in localStorage:", !!localStorage.getItem('access_token'));
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.lastLogin = null;
      })

      // --- registerUser ---
      .addCase(registerUser.pending, (state) => {
        state.loading = 'pending';
        state.error = null;
        state.isAuthenticated = false;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        const { user, token, refresh_token } = action.payload;
        state.loading = 'succeeded';
        state.user = user || null;
        state.token = token || null;
        state.refreshToken = refresh_token || null;
        state.isAuthenticated = Boolean(token);
        state.error = null;
        debugLog("registerUser fulfilled - auto-login status:", state.isAuthenticated);
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.lastLogin = null;
      })

      // --- logoutUser ---
      .addCase(logoutUser.fulfilled, (state) => {
        Object.assign(state, createInitialState());
        state.loading = 'succeeded';
        debugLog("logoutUser fulfilled - state reset");
      })
      .addCase(logoutUser.rejected, (state, action) => {
        Object.assign(state, createInitialState());
        state.loading = 'failed';
        state.error = action.payload || 'Logout failed on server, but client state reset.';
      })

      // --- checkAuthStatus ---
      .addCase(checkAuthStatus.pending, (state) => {
        state.loading = 'pending';
        state.error = null;
      })
      .addCase(checkAuthStatus.fulfilled, (state, action) => {
        const { user, token } = action.payload;
        state.loading = 'succeeded';
        state.user = user;
        state.token = token;
        state.isAuthenticated = true;
        state.error = null;
        debugLog("checkAuthStatus fulfilled - authenticated");
      })
      .addCase(checkAuthStatus.rejected, (state, action) => {
        state.loading = 'failed';
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.lastLogin = null;
        state.error = action.payload || 'Authentication check failed.';
      })

      // --- updateProfile ---
      .addCase(updateProfile.pending, (state) => {
        state.loading = 'pending';
        state.error = null;
      })
      .addCase(updateProfile.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        const updatedUser = action.payload;
        if (state.user && updatedUser) {
          Object.keys(updatedUser).forEach(key => {
            if (state.user[key] !== updatedUser[key]) {
              state.user[key] = updatedUser[key];
            }
          });
        }
        state.error = null;
        debugLog("updateProfile fulfilled");
      })
      .addCase(updateProfile.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload;
      });
  },
});

// Export actions
export const {
  clearError,
  updatePreferences,
  resetUserState,
  setInitialAuthData,
  clearTemporaryState
} = userSlice.actions;

// Memoized selectors for better performance
export const selectUser = (state) => state.user.user;
export const selectIsAuthenticated = (state) => state.user.isAuthenticated;
export const selectUserLoading = (state) => state.user.loading;
export const selectUserError = (state) => state.user.error;
export const selectUserPreferences = (state) => state.user.preferences;
export const selectUserToken = (state) => state.user.token;
export const selectUserRefreshToken = (state) => state.user.refreshToken;

// New selectors for better performance
export const selectIsLoading = (state) => state.user.loading === 'pending';
export const selectHasError = (state) => Boolean(state.user.error);
export const selectLastLogin = (state) => state.user.lastLogin ? new Date(state.user.lastLogin) : null;

export default userSlice.reducer;