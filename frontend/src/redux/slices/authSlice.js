import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { authService } from '../../services/authService'

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const response = await authService.login(email, password)
      // FIXED: authService.login already returns the processed data
      return response
    } catch (error) {
      return rejectWithValue(error.message || 'Login failed')
    }
  }
)

export const registerUser = createAsyncThunk(
  'auth/registerUser',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await authService.register(userData)
      // FIXED: authService.register already returns the processed data
      return response
    } catch (error) {
      return rejectWithValue(error.message || 'Registration failed')
    }
  }
)

export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout()
      return {}
    } catch (error) {
      return rejectWithValue(error.message || 'Logout failed')
    }
  }
)

export const checkAuthStatus = createAsyncThunk(
  'auth/checkAuthStatus',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.getCurrentUser()
      // FIXED: authService.getCurrentUser already returns the processed data
      return response
    } catch (error) {
      return rejectWithValue(error.message || 'Not authenticated')
    }
  }
)

export const updateProfile = createAsyncThunk(
  'auth/updateProfile',
  async (profileData, { rejectWithValue }) => {
    try {
      const response = await authService.updateProfile(profileData)
      // FIXED: authService.updateProfile already returns the processed data
      return response
    } catch (error) {
      return rejectWithValue(error.message || 'Profile update failed')
    }
  }
)

// FIXED: Get initial state from localStorage properly
const getInitialState = () => {
  const token = authService.getAccessToken();
  const user = authService.getStoredUser();
  const isAuthenticated = authService.isAuthenticated();
  
  return {
    user: user,
    token: token,
    isAuthenticated: isAuthenticated,
    isLoading: false,
    error: null,
    loginAttempts: 0,
    lastLoginAttempt: null,
  };
};

const initialState = getInitialState();

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    resetAuthState: (state) => {
      state.user = null
      state.token = null
      state.isAuthenticated = false
      state.error = null
      state.loginAttempts = 0
      state.lastLoginAttempt = null
      // Clear localStorage through authService
      authService.clearTokens()
    },
    incrementLoginAttempts: (state) => {
      state.loginAttempts += 1
      state.lastLoginAttempt = Date.now()
    },
    resetLoginAttempts: (state) => {
      state.loginAttempts = 0
      state.lastLoginAttempt = null
    },
    // FIXED: Add action to set auth state on app initialization
    setAuthState: (state, action) => {
      const { user, token, isAuthenticated } = action.payload
      state.user = user
      state.token = token
      state.isAuthenticated = isAuthenticated
    }
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false
        // FIXED: Use the correct structure from authService
        state.user = action.payload.user
        state.token = action.payload.token
        state.isAuthenticated = true
        state.error = null
        state.loginAttempts = 0
        state.lastLoginAttempt = null
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
        state.isAuthenticated = false
        state.user = null
        state.token = null
        state.loginAttempts += 1
        state.lastLoginAttempt = Date.now()
      })
      
      // Register
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false
        // FIXED: Use the correct structure from authService
        state.user = action.payload.user
        state.token = action.payload.token
        state.isAuthenticated = true
        state.error = null
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
        state.isAuthenticated = false
        state.user = null
        state.token = null
      })
      
      // Logout
      .addCase(logoutUser.pending, (state) => {
        state.isLoading = true
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.isLoading = false
        state.user = null
        state.token = null
        state.isAuthenticated = false
        state.error = null
        state.loginAttempts = 0
        state.lastLoginAttempt = null
      })
      .addCase(logoutUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
        // Still clear auth state even if logout fails
        state.user = null
        state.token = null
        state.isAuthenticated = false
      })
      
      // Check Auth Status
      .addCase(checkAuthStatus.pending, (state) => {
        state.isLoading = true
      })
      .addCase(checkAuthStatus.fulfilled, (state, action) => {
        state.isLoading = false
        // FIXED: Use the correct structure from authService
        state.user = action.payload.user
        state.token = action.payload.token
        state.isAuthenticated = true
        state.error = null
      })
      .addCase(checkAuthStatus.rejected, (state, action) => {
        state.isLoading = false
        state.user = null
        state.token = null
        state.isAuthenticated = false
        state.error = action.payload
      })
      
      // Update Profile
      .addCase(updateProfile.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(updateProfile.fulfilled, (state, action) => {
        state.isLoading = false
        // FIXED: Use the correct structure from authService
        state.user = action.payload.user
        state.error = null
      })
      .addCase(updateProfile.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload
      })
  },
})

export const { 
  clearError, 
  resetAuthState, 
  incrementLoginAttempts, 
  resetLoginAttempts,
  setAuthState 
} = authSlice.actions

export default authSlice.reducer

// Selectors
export const selectUser = (state) => state.auth.user
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated
export const selectIsLoading = (state) => state.auth.isLoading
export const selectAuthError = (state) => state.auth.error
export const selectLoginAttempts = (state) => state.auth.loginAttempts
export const selectToken = (state) => state.auth.token