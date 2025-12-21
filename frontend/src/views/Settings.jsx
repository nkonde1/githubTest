// src/views/Settings.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import {
  UserCircleIcon,
  BellIcon,
  ShieldCheckIcon,
  CreditCardIcon,
  GlobeAltIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import SubscriptionModal from '../components/Billing/SubscriptionModal';

const Settings = () => {
  const { user, updateUserProfile } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);

  // Initialize subscription with defaults to prevent "Overdue" flash
  const [subscription, setSubscription] = useState({
    tier: 'free_trial',
    status: 'active',
    endDate: '—',
    amount: 0,
    provider: '—'
  });

  const [telcoConnections, setTelcoConnections] = useState([]);

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    provider: '',
    company: '',
    timezone: 'UTC',
    language: 'en'
  });

  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    pushNotifications: true,
    smsAlerts: false,
    weeklyReports: true,
    securityAlerts: true,
    paymentReminders: true
  });

  const [security, setSecurity] = useState({
    twoFactorEnabled: false,
    passwordLastChanged: '2024-01-15',
    activeSessions: 2
  });

  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserCircleIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'billing', name: 'Billing', icon: CreditCardIcon },
    { id: 'preferences', name: 'Preferences', icon: GlobeAltIcon }
  ];

  useEffect(() => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  useEffect(() => {
    if (activeTab === 'billing') {
      fetchSubscriptionStatus();
    }
    // Fetch telco connections when on profile tab and user is authenticated
    if (activeTab === 'profile' && user) {
      fetchTelcoConnections();
    }
  }, [activeTab, user]);

  useEffect(() => {
    if (user) {
      const primaryTelco = telcoConnections.find(c => c.status === 'verified') || telcoConnections[0];
      setFormData({
        firstName: user.first_name || '',
        lastName: user.last_name || '',
        email: user.email || '',
        phone: primaryTelco?.wallet_number || user.phone_number || '',
        provider: primaryTelco?.provider || '',
        company: user.business_name || '',
        timezone: user.timezone || 'UTC',
        language: user.language || 'en'
      });
    }
  }, [user, telcoConnections]);

  const fetchTelcoConnections = async () => {
    try {
      const response = await api.get('/api/v1/telco/connections');
      setTelcoConnections(response.data);
    } catch (error) {
      console.error('Failed to fetch telco connections:', error);
    }
  };

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await api.get('/api/v1/billing/status');
      const data = response.data;
      setSubscription({
        tier: data.tier || 'free_trial',
        status: data.status || 'active',
        endDate: data.due_date ? new Date(data.due_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—',
        amount: data.last_payment?.amount || 0,
        provider: data.last_payment?.provider || '—'
      });
    } catch (error) {
      console.error('Failed to fetch subscription status:', error);
      setSubscription({
        tier: user?.subscription_tier || 'free_trial',
        status: user?.subscription_status || 'active',
        endDate: '—',
        amount: 0,
        provider: '—'
      });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleNotificationChange = (key) => {
    setNotifications(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      if (updateUserProfile) {
        await updateUserProfile(formData);
      }
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to update profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordUpdate = async (e) => {
    e.preventDefault();
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      alert('New passwords do not match');
      return;
    }
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to update password:', error);
    } finally {
      setLoading(false);
    }
  };

  const getNotificationDescription = (key) => {
    const descriptions = {
      emailAlerts: 'Receive important updates via email',
      pushNotifications: 'Get push notifications on your device',
      smsAlerts: 'Receive SMS alerts for critical updates',
      weeklyReports: 'Weekly summary of your account activity',
      securityAlerts: 'Notifications about security events',
      paymentReminders: 'Reminders about upcoming payments'
    };
    return descriptions[key] || '';
  };

  const formatTierName = (tier) => {
    if (!tier) return 'Free Trial';
    if (tier === '6_months') return '6 Months';
    if (tier === '12_months') return '12 Months';
    return tier.replace('_', ' ');
  };

  const renderProfileTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Profile Information</h3>
        {showSuccess && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
            <CheckCircleIcon className="w-5 h-5 text-green-600" />
            <span className="text-green-700">Profile updated successfully!</span>
          </div>
        )}
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="firstName" className="block text-sm font-medium text-gray-700">First Name</label>
              <input type="text" id="firstName" name="firstName" value={formData.firstName} onChange={handleInputChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="lastName" className="block text-sm font-medium text-gray-700">Last Name</label>
              <input type="text" id="lastName" name="lastName" value={formData.lastName} onChange={handleInputChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email Address</label>
              <input type="email" id="email" name="email" value={formData.email} onChange={handleInputChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700">Phone Number (Mobile Money)</label>
              <input type="tel" id="phone" name="phone" value={formData.phone} onChange={handleInputChange} readOnly
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50 text-gray-600" />
            </div>
            <div>
              <label htmlFor="provider" className="block text-sm font-medium text-gray-700">Provider</label>
              <input type="text" id="provider" name="provider" value={formData.provider} onChange={handleInputChange} readOnly
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50 text-gray-600 uppercase" />
            </div>
            <div>
              <label htmlFor="company" className="block text-sm font-medium text-gray-700">Business Name</label>
              <input type="text" id="company" name="company" value={formData.company} onChange={handleInputChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const renderNotificationsTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
      <div className="space-y-4">
        {Object.entries(notifications).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
            <div>
              <h4 className="text-sm font-medium text-gray-900 capitalize">{key.replace(/([A-Z])/g, ' $1').toLowerCase()}</h4>
              <p className="text-sm text-gray-500">{getNotificationDescription(key)}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" checked={value} onChange={() => handleNotificationChange(key)} className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSecurityTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Security Settings</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-900">Two-Factor Authentication</h4>
            <p className="text-sm text-gray-500">Add an extra layer of security</p>
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
            {security.twoFactorEnabled ? 'Disable' : 'Enable'}
          </button>
        </div>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <h4 className="text-sm font-medium text-gray-900 mb-4">Change Password</h4>
        <form onSubmit={handlePasswordUpdate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Current Password</label>
            <div className="relative">
              <input type={showCurrentPassword ? "text" : "password"} name="currentPassword" value={passwordForm.currentPassword} onChange={handlePasswordChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 pr-10 focus:ring-2 focus:ring-blue-500" />
              <button type="button" onClick={() => setShowCurrentPassword(!showCurrentPassword)} className="absolute inset-y-0 right-0 pr-3 flex items-center">
                {showCurrentPassword ? <EyeSlashIcon className="w-5 h-5 text-gray-400" /> : <EyeIcon className="w-5 h-5 text-gray-400" />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">New Password</label>
            <div className="relative">
              <input type={showNewPassword ? "text" : "password"} name="newPassword" value={passwordForm.newPassword} onChange={handlePasswordChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 pr-10 focus:ring-2 focus:ring-blue-500" />
              <button type="button" onClick={() => setShowNewPassword(!showNewPassword)} className="absolute inset-y-0 right-0 pr-3 flex items-center">
                {showNewPassword ? <EyeSlashIcon className="w-5 h-5 text-gray-400" /> : <EyeIcon className="w-5 h-5 text-gray-400" />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
            <input type="password" name="confirmPassword" value={passwordForm.confirmPassword} onChange={handlePasswordChange}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500" />
          </div>
          <button type="submit" disabled={loading} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Active Sessions</h4>
        <p className="text-sm text-gray-500 mb-4">You have {security.activeSessions} active sessions</p>
        <button className="text-red-600 text-sm hover:text-red-700">End all other sessions</button>
      </div>
    </div>
  );

  const renderBillingTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900">Billing & Subscription</h3>
      <div className={`border rounded-lg p-6 ${subscription?.status === 'overdue' ? 'bg-red-50 border-red-200' : 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200'}`}>
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-lg font-semibold text-gray-900">{formatTierName(subscription?.tier)}</h4>
            <p className="text-gray-600">{subscription?.status === 'overdue' ? 'Your subscription is overdue.' : 'Next billing: ' + (subscription?.endDate || '—')}</p>
            <p className="text-2xl font-bold text-blue-600 mt-2">
              {subscription?.tier === '6_months' ? 'ZMW 2,500' : subscription?.tier === '12_months' ? 'ZMW 4,500' : 'Free'}
            </p>
          </div>
          <div className="text-right">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${subscription?.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {subscription?.status === 'active' ? 'Active' : 'Overdue'}
            </span>
            <div className="mt-4">
              <button onClick={() => setShowSubscriptionModal(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 shadow-sm">
                {subscription?.tier === 'free_trial' ? 'Upgrade Plan' : 'Renew / Extend'}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-4">Payment Method</h4>
        <div className="flex items-center space-x-4">
          <div className="w-12 h-8 bg-gray-100 rounded flex items-center justify-center border">
            <span className="text-gray-600 text-xs font-bold">MOBILE</span>
          </div>
          <div>
            <p className="text-sm font-medium">Mobile Money</p>
            <p className="text-xs text-gray-500">MTN / Airtel</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPreferencesTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900">Preferences</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
          <select name="timezone" value={formData.timezone} onChange={handleInputChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500">
            <option value="UTC">UTC</option>
            <option value="EST">Eastern Time</option>
            <option value="CST">Central Time</option>
            <option value="MST">Mountain Time</option>
            <option value="PST">Pacific Time</option>
            <option value="CAT">Central Africa Time</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
          <select name="language" value={formData.language} onChange={handleInputChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500">
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
          </select>
        </div>
      </div>
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-yellow-800">Data Export</h4>
            <p className="text-sm text-yellow-700 mt-1">You can request a complete export of your account data at any time.</p>
            <button className="mt-2 text-yellow-800 text-sm font-medium hover:text-yellow-900">Request Data Export</button>
          </div>
        </div>
      </div>
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-red-800 mb-2">Danger Zone</h4>
        <p className="text-sm text-red-700 mb-4">Once you delete your account, there is no going back.</p>
        <button className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700">Delete Account</button>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile': return renderProfileTab();
      case 'notifications': return renderNotificationsTab();
      case 'security': return renderSecurityTab();
      case 'billing': return renderBillingTab();
      case 'preferences': return renderPreferencesTab();
      default: return renderProfileTab();
    }
  };

  if (loading && activeTab === 'profile') {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading settings...</span>
      </div>
    );
  }

  return (
    <div className="container page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="text-gray-600">Manage your account settings and preferences</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        <div className="w-full lg:w-64 sticky top-16 self-start">
          <nav className="space-y-1 card p-2 settings-list">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
                    ${activeTab === tab.id ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700' : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'}`}
                >
                  <Icon className="settings-item-icon mr-3" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="flex-1 settings-card">
          <div className="card">
            {renderTabContent()}
          </div>
        </div>
      </div>

      {showSubscriptionModal && (
        <SubscriptionModal
          isOpen={showSubscriptionModal}
          onClose={() => setShowSubscriptionModal(false)}
          onSuccess={() => {
            // Don't close modal immediately so user sees success message
            fetchSubscriptionStatus();
          }}
        />
      )}
    </div>
  );
};

export default Settings;