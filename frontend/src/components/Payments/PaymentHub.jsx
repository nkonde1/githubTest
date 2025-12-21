// /frontend/src/components/PaymentHub.jsx

import React, { useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  TrendingUp,
  RefreshCw,
  DollarSign,
  BarChart3,
  AlertCircle,
} from 'lucide-react';
import { fetchPaymentStats, selectPaymentStats } from '../../redux/slices/financeSlice';
import TransactionsTable from '../TransactionsTable';

const PaymentHub = () => {
  const dispatch = useDispatch();
  // Use the selector for payment stats
  const {
    total_revenue,
    transaction_count,
    success_rate,
    loading,
    error
  } = useSelector(selectPaymentStats);

  // Fetch stats on mount
  useEffect(() => {
    dispatch(fetchPaymentStats());
  }, [dispatch]);

  const handleRefresh = useCallback(() => {
    dispatch(fetchPaymentStats());
    // TransactionsTable handles its own data fetching, but we could trigger a reload if needed.
    // Since TransactionsTable listens to its own state, we might need to coordinate if we want a global refresh.
    // For now, refreshing stats is the primary action here.
  }, [dispatch]);

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'ZMW',
    }).format(value || 0);
  };

  // Summary Card Component
  const SummaryCard = ({ icon: Icon, label, value, color = 'blue' }) => {
    const colorClasses = {
      blue: 'from-blue-50 to-blue-100 border-blue-200',
      green: 'from-green-50 to-green-100 border-green-200',
      purple: 'from-purple-50 to-purple-100 border-purple-200',
    };

    const iconColors = {
      blue: 'text-blue-600',
      green: 'text-green-600',
      purple: 'text-purple-600',
    };

    return (
      <div className={`bg-gradient-to-br ${colorClasses[color]} border rounded-lg p-6 shadow-sm`}>
        <div className="flex justify-between items-start">
          <div>
            <p className="text-gray-600 text-sm font-medium mb-2">{label}</p>
            <p className="text-3xl font-bold text-gray-900">{value}</p>
          </div>
          <Icon className={`${iconColors[color]} opacity-40`} size={32} />
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-blue-50 p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-5xl font-bold text-gray-900">Payments</h1>
            <p className="text-gray-600 mt-2">Manage transactions and payment data</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <SummaryCard
            icon={DollarSign}
            label="Total Revenue"
            value={formatCurrency(total_revenue)}
            color="green"
          />
          <SummaryCard
            icon={BarChart3}
            label="Total Transactions"
            value={transaction_count?.toLocaleString() || '0'}
            color="blue"
          />
          <SummaryCard
            icon={TrendingUp}
            label="Success Rate"
            value={`${(success_rate ? success_rate * 100 : 0).toFixed(1)}%`}
            color="purple"
          />
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6 flex items-start">
          <AlertCircle className="text-red-600 mr-4 flex-shrink-0 mt-1" size={24} />
          <div>
            <h3 className="font-semibold text-red-900 mb-1">Error loading statistics</h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content - Replaced with TransactionsTable */}
      <TransactionsTable />
    </div>
  );
};

export default PaymentHub;