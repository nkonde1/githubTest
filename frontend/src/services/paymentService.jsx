// /frontend/src/services/paymentService.jsx

import api from './api'; // Assuming you have an 'api.js' or 'api.jsx' for Axios or fetch setup

const paymentService = {
  /**
   * Fetches an overview of payment statistics.
   * @param {Object} filters - Contains dateRange, status, method, search.
   * @returns {Promise<Object>} - Mock payment statistics.
   */
  getPaymentOverview: async (filters) => {
    console.log('Fetching payment overview with filters:', filters);
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock data for demonstration
    return {
      total_revenue: 125000 + Math.floor(Math.random() * 5000),
      transaction_count: 2500 + Math.floor(Math.random() * 100),
      avg_transaction_value: (Math.random() * 100 + 50).toFixed(2),
      success_rate: (95 + Math.random() * 4).toFixed(1), // 95.0% - 99.0%
      revenue_growth: (Math.random() * 5 - 2.5).toFixed(1), // -2.5% to +2.5%
      dispute_rate: (0.1 + Math.random() * 0.5).toFixed(2), // 0.1% to 0.6%
      payment_method_distribution: {
        'Credit Card': 60,
        'Bank Transfer': 25,
        'Digital Wallet': 15,
      },
      daily_revenue: Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        amount: 3000 + Math.floor(Math.random() * 1000),
      })),
    };
  },

  /**
   * Fetches a list of transactions.
   * @param {Object} params - Pagination and filter parameters (e.g., page, limit, status).
   * @returns {Promise<Object>} - Mock list of transactions.
   */
  getTransactions: async (params) => {
    console.log('Fetching transactions with params:', params);
    await new Promise(resolve => setTimeout(resolve, 700));

    const mockTransactions = Array.from({ length: params.limit || 10 }, (_, i) => ({
      id: `TXN${1000 + (params.page || 1) * 100 + i}`,
      amount: (Math.random() * 500 + 10).toFixed(2),
      currency: 'USD',
      status: ['completed', 'pending', 'failed', 'refunded'][Math.floor(Math.random() * 4)],
      method: ['card', 'bank_transfer', 'digital_wallet'][Math.floor(Math.random() * 3)],
      date: new Date(Date.now() - Math.floor(Math.random() * 30) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      customer_id: `CUST${Math.floor(Math.random() * 1000)}`,
      description: `Payment for order #${Math.floor(Math.random() * 9999)}`,
    }));

    return {
      transactions: mockTransactions,
      total_count: 100, // Total count for pagination
    };
  },

  /**
   * Fetches a list of supported payment methods and their configurations.
   * @returns {Promise<Array>} - Mock list of payment methods.
   */
  getPaymentMethods: async () => {
    console.log('Fetching payment methods...');
    await new Promise(resolve => setTimeout(resolve, 300));
    return [
      { id: 'stripe', name: 'Stripe', status: 'active', fee: '2.9% + $0.30', type: 'Credit Card, ACH' },
      { id: 'paypal', name: 'PayPal', status: 'active', fee: '3.49%', type: 'Digital Wallet' },
      { id: 'square', name: 'Square', status: 'active', fee: '2.6% + $0.10', type: 'Credit Card' },
      { id: 'bank_transfer', name: 'Bank Transfer', status: 'active', fee: '0.5%', type: 'ACH' },
      { id: 'apple_pay', name: 'Apple Pay', status: 'inactive', fee: '2.9%', type: 'Digital Wallet' },
    ];
  },

  /**
   * Fetches a list of payment disputes.
   * @returns {Promise<Object>} - Mock list of disputes.
   */
  getDisputes: async () => {
    console.log('Fetching disputes...');
    await new Promise(resolve => setTimeout(resolve, 600));
    const mockDisputes = [
      { id: 'DISP001', transaction_id: 'TXN1023', amount: 55.00, reason: 'Unauthorized transaction', status: 'pending', date: '2025-06-01' },
      { id: 'DISP002', transaction_id: 'TXN1055', amount: 120.00, reason: 'Item not received', status: 'under_review', date: '2025-05-28' },
      { id: 'DISP003', transaction_id: 'TXN1089', amount: 35.00, reason: 'Duplicate charge', status: 'resolved', date: '2025-05-20' },
      { id: 'DISP004', transaction_id: 'TXN1101', amount: 200.00, reason: 'Fraudulent activity', status: 'pending', date: '2025-06-10' },
    ];
    return { disputes: mockDisputes.filter(d => d.status !== 'resolved') }; // Only show active disputes
  },

  /**
   * Fetches payment analytics data.
   * @returns {Promise<Object>} - Mock analytics data.
   */
  getPaymentAnalytics: async () => {
    console.log('Fetching payment analytics...');
    await new Promise(resolve => setTimeout(resolve, 800));
    return {
      daily_revenue: Array.from({ length: 7 }, (_, i) => ({
        date: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        revenue: 1500 + Math.floor(Math.random() * 500),
      })),
      payment_method_breakdown: {
        'Credit Card': 70,
        'Digital Wallet': 20,
        'Bank Transfer': 10,
      },
      success_rate: 98.5,
      avg_transaction_value: 127.50,
      total_volume: 35000,
      // Add more analytics data as needed for charts/metrics
    };
  },

  /**
   * Exports payment data.
   * @param {Object} exportParams - Parameters for the export.
   * @returns {Promise<Blob>} - A mock Blob representing the exported file.
   */
  exportPayments: async (exportParams) => {
    console.log('Exporting payments with params:', exportParams);
    await new Promise(resolve => setTimeout(resolve, 1000));
    const mockData = `Transaction ID,Amount,Status,Date\nTXN1,100.00,Completed,2025-06-15\nTXN2,50.00,Pending,2025-06-16`;
    return new Blob([mockData], { type: 'text/csv' });
  },

  /**
   * Syncs payments from external sources.
   * @param {string} source - The source to sync from (e.g., 'stripe').
   * @returns {Promise<Object>} - Result of the sync operation.
   */
  syncPayments: async (source) => {
    console.log(`Syncing payments from ${source}...`);
    await new Promise(resolve => setTimeout(resolve, 1500));
    return { success: true, message: `Payments from ${source} synced successfully.` };
  },

  /**
   * Initiates reconciliation process.
   * @returns {Promise<Object>} - Result of the reconciliation.
   */
  getReconciliation: async () => {
    console.log('Initiating reconciliation...');
    await new Promise(resolve => setTimeout(resolve, 2000));
    return { success: true, message: 'Reconciliation process started.', discrepancies: 0 };
  },

  /**
   * Clears cached payment data.
   */
  clearCache: () => {
    console.log('Clearing payment service cache (mock operation)');
    // In a real app, you might clear a client-side cache or tell Redux to refetch
  },
};

export default paymentService;