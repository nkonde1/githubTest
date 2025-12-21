const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class UserService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Helper method to make API requests
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add authorization token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication methods
  async login(credentials) {
    const response = await this.makeRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    if (response.token) {
      localStorage.setItem('authToken', response.token);
    }
    
    return response;
  }

  async register(userData) {
    const response = await this.makeRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    
    if (response.token) {
      localStorage.setItem('authToken', response.token);
    }
    
    return response;
  }

  async logout() {
    try {
      await this.makeRequest('/auth/logout', {
        method: 'POST',
      });
    } finally {
      localStorage.removeItem('authToken');
    }
  }

  // User profile methods
  async fetchUserProfile() {
    return await this.makeRequest('/user/profile');
  }

  async updateUserProfile(profileData) {
    return await this.makeRequest('/user/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  async updatePassword(passwordData) {
    return await this.makeRequest('/user/password', {
      method: 'PUT',
      body: JSON.stringify(passwordData),
    });
  }

  // Business settings methods
  async getBusinessSettings() {
    return await this.makeRequest('/user/business-settings');
  }

  async updateBusinessSettings(settings) {
    return await this.makeRequest('/user/business-settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Integration methods
  async getIntegrations() {
    return await this.makeRequest('/user/integrations');
  }

  async connectIntegration(integrationData) {
    return await this.makeRequest('/user/integrations', {
      method: 'POST',
      body: JSON.stringify(integrationData),
    });
  }

  async disconnectIntegration(integrationId) {
    return await this.makeRequest(`/user/integrations/${integrationId}`, {
      method: 'DELETE',
    });
  }

  async testIntegration(integrationId) {
    return await this.makeRequest(`/user/integrations/${integrationId}/test`, {
      method: 'POST',
    });
  }

  // Notification preferences
  async getNotificationPreferences() {
    return await this.makeRequest('/user/notifications');
  }

  async updateNotificationPreferences(preferences) {
    return await this.makeRequest('/user/notifications', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  // Subscription and billing
  async getSubscription() {
    return await this.makeRequest('/user/subscription');
  }

  async updateSubscription(planId) {
    return await this.makeRequest('/user/subscription', {
      method: 'PUT',
      body: JSON.stringify({ planId }),
    });
  }

  async getBillingHistory() {
    return await this.makeRequest('/user/billing/history');
  }

  async updatePaymentMethod(paymentMethodData) {
    return await this.makeRequest('/user/billing/payment-method', {
      method: 'PUT',
      body: JSON.stringify(paymentMethodData),
    });
  }

  // API Key management
  async getApiKeys() {
    return await this.makeRequest('/user/api-keys');
  }

  async createApiKey(keyData) {
    return await this.makeRequest('/user/api-keys', {
      method: 'POST',
      body: JSON.stringify(keyData),
    });
  }

  async revokeApiKey(keyId) {
    return await this.makeRequest(`/user/api-keys/${keyId}`, {
      method: 'DELETE',
    });
  }

  // Two-factor authentication
  async enable2FA() {
    return await this.makeRequest('/user/2fa/enable', {
      method: 'POST',
    });
  }

  async disable2FA(verificationCode) {
    return await this.makeRequest('/user/2fa/disable', {
      method: 'POST',
      body: JSON.stringify({ code: verificationCode }),
    });
  }

  async verify2FA(verificationCode) {
    return await this.makeRequest('/user/2fa/verify', {
      method: 'POST',
      body: JSON.stringify({ code: verificationCode }),
    });
  }

  // Account management
  async deleteAccount(confirmationData) {
    return await this.makeRequest('/user/account', {
      method: 'DELETE',
      body: JSON.stringify(confirmationData),
    });
  }

  async downloadUserData() {
    const response = await fetch(`${this.baseURL}/user/data-export`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('authToken')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to download user data');
    }
    
    return response.blob();
  }

  // Utility methods
  isAuthenticated() {
    return !!localStorage.getItem('authToken');
  }

  getToken() {
    return localStorage.getItem('authToken');
  }

  clearToken() {
    localStorage.removeItem('authToken');
  }
}

// Create and export a singleton instance
const userService = new UserService();

// Export individual methods for easier importing
export const {
  login,
  register,
  logout,
  fetchUserProfile,
  updateUserProfile,
  updatePassword,
  getBusinessSettings,
  updateBusinessSettings,
  getIntegrations,
  connectIntegration,
  disconnectIntegration,
  testIntegration,
  getNotificationPreferences,
  updateNotificationPreferences,
  getSubscription,
  updateSubscription,
  getBillingHistory,
  updatePaymentMethod,
  getApiKeys,
  createApiKey,
  revokeApiKey,
  enable2FA,
  disable2FA,
  verify2FA,
  deleteAccount,
  downloadUserData,
  isAuthenticated,
  getToken,
  clearToken,
} = userService;

export default userService;