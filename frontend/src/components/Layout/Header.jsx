// src/components/layout/Header.jsx - Fixed error handling
import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
  selectUser, 
  selectIsAuthenticated, 
  selectUserLoading,
  checkAuthStatus 
} from '../../redux/slices/user_slice';
import { authService } from '../../services/authService';

const Header = () => {
  const dispatch = useDispatch();
  const user = useSelector(selectUser);
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isLoading = useSelector(selectUserLoading);

  useEffect(() => {
    // Only fetch user info if we have a token but no user data
    const token = authService.getAccessToken();
    
    if (token && !user && isLoading === 'idle') {
      // Wrap dispatch in try-catch and handle promise properly
      const fetchUserData = async () => {
        try {
          await dispatch(checkAuthStatus()).unwrap();
        } catch (error) {
          console.error('Header: Failed to fetch user data:', error);
          // Handle error appropriately - maybe redirect to login
        }
      };
      
      fetchUserData();
    }
  }, [dispatch, user, isLoading]);

  // Handle logout
  const handleLogout = async () => {
    try {
      await authService.logout();
      // Redirect will be handled by the auth service or context
    } catch (error) {
      console.error('Header: Logout failed:', error);
    }
  };

  // Show loading state
  if (isLoading === 'pending') {
    return (
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
            </div>
            <div className="animate-pulse">
              <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
            </div>
          </div>
        </div>
      </header>
    );
  }

  // Show authenticated header
  if (isAuthenticated && user) {
    return (
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                {user.business_name || 'Dashboard'}
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                {user.first_name} {user.last_name}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>
    );
  }

  // Fallback - shouldn't normally be reached in a protected route
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;