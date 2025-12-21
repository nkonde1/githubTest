// src/main_entry.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import App from './App.jsx';
import { store } from './redux/store.js'; // Changed from .jsx to .js
import './index.css';

/**
 * Application Entry Point
 * Sets up Redux store, React Router, AuthProvider, and renders the main App component
 * 
 * Provider hierarchy:
 * 1. Redux Provider - Global state management
 * 2. BrowserRouter - Routing context
 * 3. AuthProvider - Authentication context
 * 4. App - Main application component
 */

// Add error boundary for better error handling
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Application Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h2>Something went wrong.</h2>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Create root with error handling
const root = ReactDOM.createRoot(document.getElementById('root'));

// Add cleanup on page unload (idempotent + HMR-safe)
const handleBeforeUnload = () => {
  store.dispatch({ type: 'RESET_UI' });
  store.dispatch({ type: 'CLEAR_NOTIFICATIONS' });
  import('./services/authService').then(({ authService }) => {
    if (authService && typeof authService.cleanup === 'function') {
      authService.cleanup();
    }
  }).catch(() => {});
};

if (!window.__EFP_beforeUnloadHandlerAttached) {
  window.addEventListener('beforeunload', handleBeforeUnload);
  window.__EFP_beforeUnloadHandlerAttached = true;
}

// Ensure we don't accumulate handlers across hot reloads (Webpack)
try {
  if (typeof module !== 'undefined' && module.hot) {
    module.hot.dispose(() => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.__EFP_beforeUnloadHandlerAttached = false;
    });
  }
} catch (_) {
  // no-op
}

root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <Provider store={store}>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </Provider>
    </ErrorBoundary>
  </React.StrictMode>
);