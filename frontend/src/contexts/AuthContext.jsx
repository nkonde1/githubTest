import React, { createContext, useContext, useEffect, useMemo, useCallback, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

import {
  loginUser,
  logoutUser,
  registerUser,
  checkAuthStatus,
  updateProfile,
  clearError,
  selectUser,
  selectIsAuthenticated,
  selectUserLoading,
  selectUserError,
  selectUserToken,
  selectUserPreferences,
  setInitialAuthData,
  resetUserState
} from '../redux/slices/user_slice';

import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // Use refs to track initialization state
  const isInitialized = useRef(false);
  const isInitializing = useRef(false);

  const user = useSelector(selectUser);
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isLoading = useSelector(selectUserLoading);
  const error = useSelector(selectUserError);
  const token = useSelector(selectUserToken);
  const preferences = useSelector(selectUserPreferences);

  // Memoize user and token to prevent unnecessary re-renders
  const memoizedUser = useMemo(() => user, [user?.id, user?.email]); // Only re-compute if key fields change
  const memoizedToken = useMemo(() => token, [token]);

  console.log("AuthContext: Component rendered. Redux isLoading:", isLoading, "isAuthenticated:", isAuthenticated, "user:", !!user, "token:", !!token);

  useEffect(() => {
    // Prevent multiple initializations
    if (isInitialized.current || isInitializing.current) {
      return;
    }

    console.log("AuthContext useEffect: Running initial authentication setup.");
    isInitializing.current = true;

    const initializeAuth = async () => {
      try {
        const storedUserRaw = localStorage.getItem(authService.userKey);
        const storedToken = authService.getAccessToken();

        // Scenario 1: Already authenticated and settled
        if (isAuthenticated && isLoading === 'succeeded') {
          console.log("AuthContext useEffect: User already authenticated and settled, skipping re-check.");
          return;
        }

        // Scenario 2: Token found but not authenticated
        if (storedToken && !isAuthenticated) {
          if (isLoading === 'idle') {
            // Hydrate from localStorage first
            if (storedUserRaw && storedUserRaw !== "undefined") {
              try {
                const parsedUser = JSON.parse(storedUserRaw);
                dispatch(setInitialAuthData({
                  user: parsedUser,
                  token: storedToken,
                  isAuthenticated: true
                }));
                console.log("AuthContext useEffect: Hydrated Redux state from localStorage.");
              } catch (e) {
                console.error("AuthContext useEffect: Error parsing user data:", e);
                authService.clearTokens();
                dispatch(resetUserState());
              }
            }

            // Verify with backend
            console.log("AuthContext useEffect: Dispatching checkAuthStatus for verification.");
            await dispatch(checkAuthStatus());
          }
        } else if (!storedToken && (isAuthenticated || user || token) && isLoading !== 'pending') {
          // Scenario 3: No token but Redux shows authenticated
          console.log("AuthContext useEffect: No local token but Redux shows auth. Clearing state.");
          dispatch(logoutUser());
        } else if (!storedToken && !isAuthenticated && isLoading === 'idle') {
          // Scenario 4: Clean state
          console.log("AuthContext useEffect: Clean state confirmed.");
          if (user || token) {
            dispatch(resetUserState());
          }
        }
      } catch (error) {
        console.error("AuthContext initialization error:", error);
        dispatch(resetUserState());
      } finally {
        isInitializing.current = false;
        isInitialized.current = true;
      }
    };

    initializeAuth();
  }, [dispatch, isAuthenticated, isLoading]); // Removed user and token from dependencies

  const authLogin = useCallback(async (credentials) => {
    console.log("AuthContext: login function called.");
    try {
      const resultAction = await dispatch(loginUser(credentials)).unwrap();
      console.log('AuthContext: User logged in successfully:', resultAction.email);
      navigate('/dashboard');
      return { success: true, user: resultAction };
    } catch (err) {
      console.error('AuthContext: Login error:', err);
      return { success: false, error: err };
    }
  }, [dispatch, navigate]);

  const authLogout = useCallback(async () => {
    console.log("AuthContext: logout function called.");
    try {
      await dispatch(logoutUser()).unwrap();
      console.log('AuthContext: User logged out successfully.');
    } catch (err) {
      console.error('AuthContext: Logout error:', err);
    } finally {
      // Reset initialization state
      isInitialized.current = false;
      navigate('/login');
    }
  }, [dispatch, navigate]);

  const authRegister = useCallback(async (userData) => {
    console.log("AuthContext: register function called.");
    try {
      const resultAction = await dispatch(registerUser(userData)).unwrap();
      console.log('AuthContext: User registered successfully:', resultAction.email || 'user data missing');
      
      if (resultAction.token) {
        navigate('/dashboard');
      } else {
        navigate('/login?registrationSuccess=true');
      }
      return { success: true, user: resultAction };
    } catch (err) {
      console.error('AuthContext: Registration error:', err);
      return { success: false, error: err };
    }
  }, [dispatch, navigate]);

  const authUpdateProfile = useCallback(async (profileData) => {
    console.log("AuthContext: updateProfile function called.");
    try {
      const resultAction = await dispatch(updateProfile(profileData)).unwrap();
      console.log('AuthContext: User profile updated successfully:', resultAction);
      return { success: true, user: resultAction };
    } catch (err) {
      console.error('AuthContext: Profile update error:', err);
      return { success: false, error: err };
    }
  }, [dispatch]);

  const hasPermission = useCallback((requiredPermissions) => {
    console.warn("hasPermission function is a placeholder. Implement your actual permission logic.");
    return true;
  }, []);

  // Memoize context value with stable references
  const contextValue = useMemo(() => ({
    user: memoizedUser,
    isAuthenticated,
    isLoading,
    error,
    token: memoizedToken,
    preferences,
    login: authLogin,
    logout: authLogout,
    register: authRegister,
    updateProfile: authUpdateProfile,
    clearError: () => dispatch(clearError()),
    hasPermission,
  }), [
    memoizedUser,
    isAuthenticated,
    isLoading,
    error,
    memoizedToken,
    preferences,
    authLogin,
    authLogout,
    authRegister,
    authUpdateProfile,
    dispatch,
    hasPermission
  ]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};