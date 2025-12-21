import React from 'react';
import { 
  ExclamationTriangleIcon, 
  ArrowPathIcon,
  HomeIcon,
  BugAntIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';

/**
 * ErrorBoundary Component - Catches JavaScript errors anywhere in the child component tree
 * Features: Error logging, user-friendly error display, recovery options, and detailed error info
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
      errorId: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { 
      hasError: true,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    this.setState({
      error,
      errorInfo
    });

    // Log to console for development
    console.group('🚨 Error Boundary Caught Error');
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Component Stack:', errorInfo.componentStack);
    console.groupEnd();

    // Log to external service in production
    this.logErrorToService(error, errorInfo);
  }

  /**
   * Log error to external monitoring service
   * In production, this would integrate with services like Sentry, LogRocket, etc.
   */
  logErrorToService = (error, errorInfo) => {
    const errorData = {
      id: this.state.errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      userId: this.props.userId || 'anonymous',
      retryCount: this.state.retryCount
    };

    // In development, just log to console
    if (process.env.NODE_ENV === 'development') {
      console.log('Error logged (dev mode):', errorData);
      return;
    }

    // In production, send to monitoring service
    try {
      fetch('/api/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorData)
      }).catch(err => {
        console.error('Failed to log error to service:', err);
      });
    } catch (err) {
      console.error('Failed to log error to service:', err);
    }
  };

  /**
   * Retry the failed component
   */
  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
      retryCount: prevState.retryCount + 1
    }));
  };

  /**
   * Navigate to home page
   */
  handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  /**
   * Reload the entire page
   */
  handleReload = () => {
    window.location.reload();
  };

  /**
   * Toggle error details visibility
   */
  toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails
    }));
  };

  /**
   * Get user-friendly error message based on error type
   */
  getUserFriendlyMessage = (error) => {
    if (!error) return 'An unexpected error occurred';

    const message = error.message?.toLowerCase() || '';
    
    if (message.includes('network') || message.includes('fetch')) {
      return 'Network connection error. Please check your internet connection and try again.';
    }
    
    if (message.includes('chunk') || message.includes('loading')) {
      return 'Failed to load application resources. Please refresh the page.';
    }
    
    if (message.includes('permission') || message.includes('unauthorized')) {
      return 'You don\'t have permission to access this resource. Please contact support.';
    }
    
    if (message.includes('timeout')) {
      return 'The request timed out. Please try again.';
    }

    return 'Something went wrong. Our team has been notified and is working on a fix.';
  };

  render() {
    if (this.state.hasError) {
      const userMessage = this.getUserFriendlyMessage(this.state.error);
      const isDevelopment = process.env.NODE_ENV === 'development';

      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            
            {/* Error Icon */}
            <div className="flex justify-center mb-4">
              <div className="bg-red-100 p-3 rounded-full">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
              </div>
            </div>

            {/* Error Title */}
            <div className="text-center mb-4">
              <h1 className="text-xl font-semibold text-gray-900 mb-2">
                Oops! Something went wrong
              </h1>
              <p className="text-gray-600 text-sm">
                {userMessage}
              </p>
            </div>

            {/* Error ID (for support) */}
            {this.state.errorId && (
              <div className="bg-gray-50 rounded-lg p-3 mb-4">
                <p className="text-xs text-gray-500">
                  Error ID: <span className="font-mono">{this.state.errorId}</span>
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="space-y-3 mb-4">
              <button
                onClick={this.handleRetry}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
              >
                <ArrowPathIcon className="h-4 w-4" />
                <span>Try Again</span>
              </button>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={this.handleGoHome}
                  className="bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2 text-sm"
                >
                  <HomeIcon className="h-4 w-4" />
                  <span>Go Home</span>
                </button>

                <button
                  onClick={this.handleReload}
                  className="bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2 text-sm"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                  <span>Reload</span>
                </button>
              </div>
            </div>

            {/* Error Details (Development/Debug) */}
            {(isDevelopment || this.props.showDetails) && this.state.error && (
              <div className="border-t border-gray-200 pt-4">
                <button
                  onClick={this.toggleDetails}
                  className="w-full flex items-center justify-between text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <BugAntIcon className="h-4 w-4" />
                    <span>Error Details</span>
                  </div>
                  {this.state.showDetails ? (
                    <ChevronUpIcon className="h-4 w-4" />
                  ) : (
                    <ChevronDownIcon className="h-4 w-4" />
                  )}
                </button>

                {this.state.showDetails && (
                  <div className="mt-3 space-y-3">
                    {/* Error Message */}
                    <div>
                      <h4 className="text-xs font-medium text-gray-700 mb-1">Error Message:</h4>
                      <div className="bg-red-50 border border-red-200 rounded p-2">
                        <code className="text-xs text-red-800 break-all">
                          {this.state.error.message}
                        </code>
                      </div>
                    </div>

                    {/* Stack Trace */}
                    {this.state.error.stack && (
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 mb-1">Stack Trace:</h4>
                        <div className="bg-gray-50 border border-gray-200 rounded p-2 max-h-32 overflow-y-auto">
                          <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                            {this.state.error.stack}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Component Stack */}
                    {this.state.errorInfo?.componentStack && (
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 mb-1">Component Stack:</h4>
                        <div className="bg-gray-50 border border-gray-200 rounded p-2 max-h-32 overflow-y-auto">
                          <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Retry Count */}
                    {this.state.retryCount > 0 && (
                      <div className="text-xs text-gray-500">
                        Retry attempts: {this.state.retryCount}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Support Message */}
            <div className="text-center mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                If this problem persists, please contact{' '}
                <a 
                  href="mailto:support@financeai.com" 
                  className="text-blue-600 hover:text-blue-800"
                >
                  support@financeai.com
                </a>
                {this.state.errorId && (
                  <span> and include the error ID above.</span>
                )}
              </p>
            </div>
          </div>
        </div>
      );
    }

    // If no error, render children normally
    return this.props.children;
  }
}

/**
 * Higher-order component to wrap components with error boundary
 */
export const withErrorBoundary = (Component, errorBoundaryProps = {}) => {
  const WrappedComponent = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

/**
 * Hook to handle async errors in functional components
 */
export const useErrorHandler = () => {
  const handleError = (error) => {
    // This will trigger the nearest error boundary
    throw error;
  };

  return handleError;
};

export default ErrorBoundary;