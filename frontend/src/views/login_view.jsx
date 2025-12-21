import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Navigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

import { loginUser, clearError, selectIsAuthenticated, selectIsLoading } from '../redux/slices/user_slice';
import LoadingSpinner from '../components/common/LoadingSpinner';

/**
 * Login View Component
 * Handles user authentication with email/password
 */
const Login = () => {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isLoading = useSelector(selectIsLoading);
  const error = useSelector(state => state.user.error);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Clear any existing errors when component mounts
  useEffect(() => {
    dispatch(clearError());
  }, [dispatch]);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error when user starts typing
    if (error) {
      dispatch(clearError());
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.email || !formData.password) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      await dispatch(loginUser({
        ...formData,
        rememberMe
      })).unwrap();

      toast.success('Login successful!');
    } catch (error) {
      toast.error(error.message || 'Login failed');
    }
  };

  return (
    <div className="login-page">
      <div className="auth-container">
        {/* Header */}
        <div className="brand">
          <div className="logo">Easy</div>
          <p></p>
          <p>It is easy to sign in to your EasyFlow account</p>
        </div>

        {/* Login Form */}
        <div className="card">
          <form className="form" onSubmit={handleSubmit}>
            {/* Email Field */}
            <div className="field">
              <label htmlFor="email">Email address</label>
              <div className="input-group">
                <span className="icon left"><Mail size={18} /></span>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="input"
                  placeholder="Enter your email"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="field">
              <label htmlFor="password">Password</label>
              <div className="input-group">
                <span className="icon left"><Lock size={18} /></span>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="input with-right-icon"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="icon-btn right"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="alert error">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            {/* Remember Me & Forgot Password */}
            <div className="row between">
              <label className="checkbox">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Remember me</span>
              </label>

              <div className="link-sm">
                <Link to="/forgot-password">Forgot your password?</Link>
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button type="submit" disabled={isLoading} className="btn primary w-full">
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-8">Signing in...</span>
                  </>
                ) : (
                  'Sign in'
                )}
              </button>
            </div>

          </form>
        </div>

        {/* Sign Up Link */}
        <div className="footer-text">
          <p>
            Don't have an account? <Link to="/signup">Sign up for free</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;