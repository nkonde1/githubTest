// src/components/common/ProtectedRoute.jsx
import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  selectUser,
  selectIsAuthenticated,
  selectUserLoading,
  checkAuthStatus,
} from '../../redux/slices/user_slice';
import { authService } from '../../services/authService';
import LoadingSpinner from './LoadingSpinner';

const ProtectedRoute = ({ children }) => {
  const dispatch = useDispatch();

  const user = useSelector(selectUser);
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isLoading = useSelector(selectUserLoading);
  const reduxToken = useSelector(state => state.user.token);

  // Use authService to get token from localStorage
  const localStorageToken = authService.getAccessToken();

  console.log('ProtectedRoute: Rendered');
  console.log('ProtectedRoute: localStorageToken =', !!localStorageToken);
  console.log('ProtectedRoute: Redux isAuthenticated =', isAuthenticated);
  console.log('ProtectedRoute: Redux isLoading =', isLoading);
  console.log('ProtectedRoute: Redux user exists =', !!user);

  useEffect(() => {
    // Only dispatch checkAuthStatus if we have a token but aren't authenticated
    // and we're not already loading
    if (localStorageToken && !isAuthenticated && isLoading === 'idle') {
      console.log('ProtectedRoute useEffect: Dispatching checkAuthStatus()');
      dispatch(checkAuthStatus()).catch(error => {
        console.error('ProtectedRoute: checkAuthStatus failed:', error);
      });
    }
  }, [dispatch, localStorageToken, isAuthenticated, isLoading]);

  // Show loading spinner while checking authentication
  if (isLoading === 'pending') {
    console.log('ProtectedRoute: Showing LoadingSpinner (checking auth)');
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // Show loading spinner if we have a token but haven't verified it yet
  if (localStorageToken && !isAuthenticated && isLoading === 'idle') {
    console.log('ProtectedRoute: Showing LoadingSpinner (token exists but not verified)');
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // If no token or authentication failed, redirect to login
  if (!localStorageToken || (!isAuthenticated && isLoading !== 'pending')) {
    console.log('ProtectedRoute: Not authenticated, redirecting to /login');
    return <Navigate to="/login" replace />;
  }

  // If authenticated, render children
  if (isAuthenticated) {
    console.log('ProtectedRoute: Authenticated, rendering children');
    return children;
  }

  // Fallback: show loading spinner
  console.log('ProtectedRoute: Fallback loading state');
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <LoadingSpinner size="large" />
    </div>
  );
};

export default ProtectedRoute;