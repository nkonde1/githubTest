// src/App.jsx
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Components
import ProtectedRoute from './components/common/ProtectedRoute';
import Layout from './components/Layout/Layout';

// Views
import Login from './views/login_view';
import Signup from './views/signup_view';
import LandingPage from './views/LandingPage';
import Dashboard from './views/Dashboard';
import PaymentHub from './components/Payments/PaymentHub';
import FinancingOffers from './components/Financing/financing_page';
import Analytics from './components/Analytics/analytics_page';
import AIChat from './components/AIChat/AIChat';
import NotFound from './views/NotFound';
import Settings from './views/Settings';

// Styles
import './index.css';

function App() {
  return (
    <div className="App">
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protected Routes with Layout */}
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/*" element={<Dashboard />} />
          <Route path="/payments" element={<PaymentHub />} />
          <Route path="/payments/*" element={<PaymentHub />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/analytics/*" element={<Analytics />} />
          <Route path="/financing" element={<FinancingOffers />} />
          <Route path="/financing/*" element={<FinancingOffers />} />
          <Route path="/ai-chat" element={<AIChat />} />
          <Route path="/ai-chat/*" element={<AIChat />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/settings/*" element={<Settings />} />
        </Route>

        {/* 404 Fallback */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}

export default App;