/**
 * PaymentOverview - Overview tab component for payment analytics
 * Displays revenue trends, payment methods breakdown, and key performance indicators
 */

import React, { useState, useEffect } from 'react';
import { TrendingUp, Users, Clock, DollarSign, CreditCard, Smartphone } from 'lucide-react';
import paymentService from '../../services/paymentService';
import PaymentChart from './PaymentChart';

const PaymentOverview = () => {
  const [chartData, setChartData] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOverviewData();
  }, []);

  const loadOverviewData = async () => {
    try {
      setLoading(true);
      const [analyticsData, methodsData] = await Promise.all([
        paymentService.getPaymentAnalytics(),
        paymentService.getPaymentMethodsBreakdown()
      ]);

      setChartData(analyticsData.daily_revenue || []);
      setPaymentMethods(methodsData.methods || [
        { name: 'Credit Card', percentage: 65.2, amount: 125000, icon: CreditCard },
        { name: 'Bank Transfer', percentage: 22.8, amount: 43750, icon: DollarSign },
        { name: 'Digital Wallet', percentage: 12.0, amount: 23000, icon: Smartphone }
      ]);
    } catch (error) {
      console.error('Failed to load overview data:', error);
      setError('Failed to load payment overview data');
    } finally {
      setLoading(false);
    }
  };

  const keyMetrics = [
    {
      title: 'Avg Transaction Value',
      value: '$127.50',
      change: '+5.2%',
      icon: TrendingUp,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Active Customers',
      value: '1,247',
      change: '+12.3%',
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Avg Processing Time',
      value: '2.3s',
      change: '-0.5s',
      icon: Clock,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ];

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <div className="text-red-600 mb-2">Error loading data</div>
        <button 
          onClick={loadOverviewData}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {keyMetrics.map((metric, index) => (
          <div key={index} className={`${metric.bgColor} rounded-lg p-4`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${metric.color}`}>
                  {metric.title}
                </p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {metric.value}
                </p>
                <p className={`text-sm mt-1 ${
                  metric.change.startsWith('+') ? 'text-green-600' : 
                  metric.change.startsWith('-') && metric.title.includes('Time') ? 'text-green-600' : 'text-red-600'
                }`}>
                  {metric.change} from last month
                </p>
              </div>
              <metric.icon className={`h-8 w-8 ${metric.color}`} />
            </div>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend Chart */}
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Trend</h3>
          <PaymentChart 
            data={chartData} 
            type="line"
            height={280}
            xKey="date"
            yKey="amount"
          />
        </div>

        {/* Payment Methods Breakdown */}
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Methods</h3>
          <div className="space-y-4">
            {paymentMethods.map((method, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white rounded-lg">
                    <method.icon className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{method.name}</p>
                    <p className="text-sm text-gray-600">
                      ${method.amount?.toLocaleString() || '0'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-lg font-semibold text-green-600">
                    {method.percentage}%
                  </span>
                  <div className="w-20 bg-gray-200 rounded-full h-2 mt-1">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${method.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">98.5%</div>
          <div className="text-sm text-gray-600">Success Rate</div>
        </div>
        <div className="bg-white rounded-lg border p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">$2.1M</div>
          <div className="text-sm text-gray-600">Monthly Volume</div>
        </div>
        <div className="bg-white rounded-lg border p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">1.2%</div>
          <div className="text-sm text-gray-600">Refund Rate</div>
        </div>
        <div className="bg-white rounded-lg border p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">24</div>
          <div className="text-sm text-gray-600">Avg Days to Settle</div>
        </div>
      </div>
    </div>
  );
};

export default PaymentOverview;