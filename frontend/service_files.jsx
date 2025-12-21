// analyticsService.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const analyticsService = {
  async getAnalytics(timeRange = '30d') {
    try {
      const response = await fetch(`${API_BASE_URL}/analytics?timeRange=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch analytics');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Analytics service error:', error);
      // Return mock data for development
      return {
        dashboard: {
          revenue: 125000,
          profit: 35000,
          orders: 1250,
          cac: 45,
          ltv: 280,
          roas: 4.2
        },
        salesData: [
          { date: '2024-01-01', revenue: 12000, orders: 120, profit: 3500 },
          { date: '2024-01-02', revenue: 15000, orders: 150, profit: 4200 },
          { date: '2024-01-03', revenue: 18000, orders: 180, profit: 5100 },
          { date: '2024-01-04', revenue: 14000, orders: 140, profit: 3800 },
          { date: '2024-01-05', revenue: 16000, orders: 160, profit: 4600 }
        ],
        profitabilityData: [
          { sku: 'SKU-001', profit: 5000, margin: 32 },
          { sku: 'SKU-002', profit: 4200, margin: 28 },
          { sku: 'SKU-003', profit: 3800, margin: 25 },
          { sku: 'SKU-004', profit: 3200, margin: 22 },
          { sku: 'SKU-005', profit: 2800, margin: 18 }
        ]
      };
    }
  },

  async getSkuAnalytics(sku) {
    try {
      const response = await fetch(`${API_BASE_URL}/analytics/sku/${sku}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch SKU analytics');
      }
      
      return await response.json();
    } catch (error) {
      console.error('SKU analytics service error:', error);
      throw error;
    }
  }
};

// financingService.js
export const financingService = {
  async getFinancingOffers() {
    try {
      const response = await fetch(`${API_BASE_URL}/financing/offers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch financing offers');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Financing service error:', error);
      // Return mock data for development
      return {
        offers: [
          {
            id: 1,
            lenderName: 'Business Capital Partners',
            maxAmount: 50000,
            interestRate: 8.5,
            termMonths: 24,
            approvalTime: '24-48 hours',
            recommended: true,
            features: [
              'No collateral required',
              'Flexible repayment terms',
              'Fast approval process'
            ]
          },
          {
            id: 2,
            lenderName: 'QuickFund Solutions',
            maxAmount: 25000,
            interestRate: 12.0,
            termMonths: 18,
            approvalTime: '2-4 hours',
            recommended: false,
            features: [
              'Same-day funding',
              'Minimal documentation',
              'Online application'
            ]
          },
          {
            id: 3,
            lenderName: 'Growth Capital Inc',
            maxAmount: 100000,
            interestRate: 6.5,
            termMonths: 36,
            approvalTime: '3-5 days',
            recommended: false,
            features: [
              'Low interest rates',
              'Extended terms',
              'Relationship banking'
            ]
          }
        ],
        cashFlow: 15000,
        creditScore: 720
      };
    }
  },

  async applyForLoan(applicationData) {
    try {
      const response = await fetch(`${API_BASE_URL}/financing/apply`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(applicationData)
      });
      
      if (!response.ok) {
        throw new Error('Failed to submit loan application');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Loan application error:', error);
      throw error;
    }
  }
};

// paymentService.js
export const paymentService = {
  async getPaymentData(timeRange = '30d') {
    try {
      const response = await fetch(`${API_BASE_URL}/payments?timeRange=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch payment data');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Payment service error:', error);
      // Return mock data for development
      return {
        transactions: [
          {
            id: 1,
            amount: 125.00,
            date: '2024-01-15',
            customer: 'John Doe',
            method: 'Credit Card',
            status: 'completed'
          },
          {
            id: 2,
            amount: 89.99,
            date: '2024-01-15',
            customer: 'Jane Smith',
            method: 'PayPal',
            status: 'completed'
          },
          {
            id: 3,
            amount: 299.99,
            date: '2024-01-14',
            customer: 'Bob Johnson',
            method: 'Bank Transfer',
            status: 'pending'
          }
        ],
        totalRevenue: 125000,
        monthlyRevenue: 15000,
        paymentMethods: [
          { name: 'Credit Card', percentage: 65 },
          { name: 'PayPal', percentage: 25 },
          { name: 'Bank Transfer', percentage: 10 }
        ]
      };
    }
  },

  async syncPaymentData() {
    try {
      const response = await fetch(`${API_BASE_URL}/payments/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to sync payment data');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Payment sync error:', error);
      throw error;
    }
  }
};