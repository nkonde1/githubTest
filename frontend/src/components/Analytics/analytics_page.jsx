import api from '../../services/api';
import React, { useEffect, useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RefreshCw, BarChart3, TrendingUp, DollarSign } from 'lucide-react';
import { fetchBusinessMetrics } from '../../redux/slices/metricsSlice';

const Analytics = () => {
  const dispatch = useDispatch();
  const { metricsData, loading, error } = useSelector((state) => state.metrics);
  const token = useSelector((state) => state.user?.token);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (token) {
      dispatch(fetchBusinessMetrics(token));
    }
  }, [dispatch, token]);

  const handleRefresh = useCallback(async () => {
    if (!token) return;
    setRefreshing(true);
    try {
      await api.post('/api/v1/metrics/business_metrics/update');
      // Re-fetch metrics via Redux to update state
      dispatch(fetchBusinessMetrics(token));
    } catch (err) {
      console.error('Refresh failed', err);
    } finally {
      setRefreshing(false);
    }
  }, [dispatch, token]);

  if (loading && !refreshing && !metricsData) return <div className="p-6">Loading analytics metrics...</div>;
  if (error) return <div className="p-6 text-red-600">Error loading metrics: {error.message || JSON.stringify(error)}</div>;

  // Ensure metricsData is an array
  const metrics = Array.isArray(metricsData) ? metricsData : (metricsData ? [metricsData] : []);

  // Show latest period first
  const latest = metrics.length > 0 ? metrics[0] : {};

  const fmt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString());

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-blue-50 p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-5xl font-bold text-gray-900">Analytics</h1>
            <p className="text-gray-600 mt-2">View detailed business performance and trends</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50"
          >
            <RefreshCw size={20} className={refreshing ? 'animate-spin' : ''} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-600">Monthly revenue</div>
          <div className="text-xl font-bold">
            {(() => {
              // Calculate ZMW revenue from revenueByCurrency if available
              if (latest.revenueByCurrency) {
                const ratesToZMW = { 'USD': 27.0, 'EUR': 28.0, 'ZMW': 1.0, 'GBP': 34.0 };
                let totalZMW = 0;
                Object.entries(latest.revenueByCurrency).forEach(([curr, amt]) => {
                  totalZMW += amt * (ratesToZMW[curr] || 27.0);
                });
                return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'ZMW' }).format(totalZMW);
              }
              // Fallback for legacy data (assume USD and convert)
              return latest.monthly_revenue ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'ZMW' }).format(latest.monthly_revenue * 27.0) : '—';
            })()}
          </div>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-600">Cash flow</div>
          <div className="text-xl font-bold">
            {(() => {
              // Cash flow is typically same as revenue for this simple model, or we convert if it's a separate field
              // Assuming cash_flow in DB is USD (from AnalyticsEngine), convert to ZMW
              return latest.cash_flow ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'ZMW' }).format(latest.cash_flow * 27.0) : '—';
            })()}
          </div>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-600">Profit margin</div>
          <div className="text-xl font-bold">{latest.profit_margin ? `${(Number(latest.profit_margin) * 100).toFixed(1)}%` : '—'}</div>
        </div>
      </div>

      <div className="bg-white p-4 rounded shadow">
        <h2 className="font-medium mb-2">Detailed metrics (latest period)</h2>
        <table className="w-full text-left">
          <tbody>
            <tr><td className="py-1 text-gray-600">Customer count</td><td className="py-1">{fmt(latest.customer_count)}</td></tr>
            <tr><td className="py-1 text-gray-600">Avg order value</td><td className="py-1">{latest.avg_order_value ? `ZMW ${fmt(latest.avg_order_value * 27.0)}` : '—'}</td></tr>
            <tr><td className="py-1 text-gray-600">Repeat customer rate</td><td className="py-1">{latest.repeat_customer_rate ? `${(Number(latest.repeat_customer_rate) * 100).toFixed(1)}%` : '—'}</td></tr>
            <tr><td className="py-1 text-gray-600">Inventory turnover</td><td className="py-1">{latest.inventory_turnover ?? '—'}</td></tr>
            <tr><td className="py-1 text-gray-600">Chargeback rate</td><td className="py-1">{latest.chargeback_rate ? `${(Number(latest.chargeback_rate) * 100).toFixed(2)}%` : '—'}</td></tr>
          </tbody>
        </table>
      </div>

      {/* If you want to show multiple periods */}
      {metrics.length > 1 && (
        <div className="mt-6">
          <h3 className="font-medium mb-2">Previous periods</h3>
          <ul className="space-y-2">
            {metrics.slice(1).map((m, index) => (
              <li key={m.id || index} className="bg-white p-3 rounded shadow">
                <div className="text-sm text-gray-600">{new Date(m.period_start).toLocaleDateString()} — {new Date(m.period_end).toLocaleDateString()}</div>
                <div className="font-semibold">{m.monthly_revenue ? `ZMW ${fmt(m.monthly_revenue * 27.0)}` : '—'}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Analytics;