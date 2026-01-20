// financingService.js
import api from './api';

export const financingService = {
  async getFinancingOffers(creditScore) {
    try {
      // Pass credit score if available to get tailored offers
      const query = creditScore ? `?score=${creditScore}` : '';
      // Use api client which handles base URL and auth headers
      // Path must include /api/v1 prefix as the router is mounted there
      const response = await api.get(`/api/v1/financing/offers${query}`);
      return response.data;
    } catch (error) {
      console.error('Financing service error:', error);
      throw error;
    }
  },

  async getCreditScore() {
    try {
      const response = await api.get('/api/v1/financing/score');
      return response.data;
    } catch (error) {
      console.error('Credit score service error:', error);
      throw error;
    }
  },

  async applyForLoan(applicationData) {
    try {
      const response = await api.post('/api/v1/financing/apply', applicationData);
      return response.data;
    } catch (error) {
      console.error('Loan application error:', error);
      throw error;
    }
  }
};