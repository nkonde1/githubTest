import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import Button from '../components/Button';
import { updateUserProfile, fetchUserProfile } from '../services/userService';
import { setUser, setLoading } from '../state/actions';

const Profile = () => {
  const dispatch = useDispatch();
  const { user, loading } = useSelector(state => state.user);
  
  const [formData, setFormData] = useState({
    businessName: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    zipCode: '',
    industry: '',
    businessType: '',
    taxId: '',
    website: ''
  });
  
  const [integrations, setIntegrations] = useState({
    shopify: false,
    quickbooks: false,
    stripe: false,
    paypal: false,
    googleAds: false,
    facebookAds: false
  });

  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    paymentNotifications: true,
    financingOffers: true,
    weeklyReports: true,
    marketingInsights: false
  });

  const [activeSection, setActiveSection] = useState('profile');
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    dispatch(setLoading(true));
    try {
      const userData = await fetchUserProfile();
      setFormData({
        businessName: userData.businessName || '',
        email: userData.email || '',
        phone: userData.phone || '',
        address: userData.address || '',
        city: userData.city || '',
        state: userData.state || '',
        zipCode: userData.zipCode || '',
        industry: userData.industry || '',
        businessType: userData.businessType || '',
        taxId: userData.taxId || '',
        website: userData.website || ''
      });
      setIntegrations(userData.integrations || integrations);
      setNotifications(userData.notifications || notifications);
      dispatch(setUser(userData));
    } catch (error) {
      console.error('Error loading user profile:', error);
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleIntegrationToggle = (integration) => {
    setIntegrations(prev => ({
      ...prev,
      [integration]: !prev[integration]
    }));
  };

  const handleNotificationToggle = (notification) => {
    setNotifications(prev => ({
      ...prev,
      [notification]: !prev[notification]
    }));
  };

  const handleSaveProfile = async () => {
    try {
      dispatch(setLoading(true));
      const updatedUser = await updateUserProfile({
        ...formData,
        integrations,
        notifications
      });
      dispatch(setUser(updatedUser));
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      dispatch(setLoading(false));
    }
  };

  const menuItems = [
    { id: 'profile', label: 'Business Profile', icon: '🏢' },
    { id: 'integrations', label: 'Integrations', icon: '🔗' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
    { id: 'security', label: 'Security', icon: '🔐' },
    { id: 'billing', label: 'Billing', icon: '💳' }
  ];

  const renderProfileSection = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Business Profile</h2>
        <Button 
          onClick={() => isEditing ? handleSaveProfile() : setIsEditing(true)}
          variant={isEditing ? "primary" : "secondary"}
          disabled={loading}
        >
          {isEditing ? 'Save Changes' : 'Edit Profile'}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Name *
          </label>
          <input
            type="text"
            name="businessName"
            value={formData.businessName}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Address *
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Number
          </label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Website
          </label>
          <input
            type="url"
            name="website"
            value={formData.website}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Address
          </label>
          <input
            type="text"
            name="address"
            value={formData.address}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            City
          </label>
          <input
            type="text"
            name="city"
            value={formData.city}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            State
          </label>
          <select
            name="state"
            value={formData.state}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          >
            <option value="">Select State</option>
            <option value="CA">California</option>
            <option value="NY">New York</option>
            <option value="TX">Texas</option>
            <option value="FL">Florida</option>
            {/* Add more states as needed */}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ZIP Code
          </label>
          <input
            type="text"
            name="zipCode"
            value={formData.zipCode}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Industry
          </label>
          <select
            name="industry"
            value={formData.industry}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          >
            <option value="">Select Industry</option>
            <option value="retail">Retail</option>
            <option value="ecommerce">E-commerce</option>
            <option value="food">Food & Beverage</option>
            <option value="fashion">Fashion</option>
            <option value="electronics">Electronics</option>
            <option value="health">Health & Beauty</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Type
          </label>
          <select
            name="businessType"
            value={formData.businessType}
            onChange={handleInputChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          >
            <option value="">Select Business Type</option>
            <option value="llc">LLC</option>
            <option value="corporation">Corporation</option>
            <option value="partnership">Partnership</option>
            <option value="sole_proprietorship">Sole Proprietorship</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tax ID (EIN)
          </label>
          <input
            type="text"
            name="taxId"
            value={formData.taxId}
            onChange={handleInputChange}
            disabled={!isEditing}
            placeholder="XX-XXXXXXX"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
          />
        </div>
      </div>
    </div>
  );

  const renderIntegrationsSection = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Connected Integrations</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { key: 'shopify', name: 'Shopify', description: 'E-commerce platform integration', icon: '🛒' },
          { key: 'quickbooks', name: 'QuickBooks', description: 'Accounting and bookkeeping', icon: '📊' },
          { key: 'stripe', name: 'Stripe', description: 'Payment processing', icon: '💳' },
          { key: 'paypal', name: 'PayPal', description: 'Payment processing', icon: '🅿️' },
          { key: 'googleAds', name: 'Google Ads', description: 'Advertising analytics', icon: '🎯' },
          { key: 'facebookAds', name: 'Facebook Ads', description: 'Social media advertising', icon: '📱' }
        ].map((integration) => (
          <div key={integration.key} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{integration.icon}</span>
                <div>
                  <h3 className="font-medium text-gray-900">{integration.name}</h3>
                  <p className="text-sm text-gray-500">{integration.description}</p>
                </div>
              </div>
              <button
                onClick={() => handleIntegrationToggle(integration.key)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  integrations[integration.key] ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    integrations[integration.key] ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            {integrations[integration.key] && (
              <div className="mt-3 flex items-center text-sm text-green-600">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Connected
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderNotificationsSection = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Notification Preferences</h2>
      
      <div className="space-y-4">
        {[
          { key: 'emailAlerts', name: 'Email Alerts', description: 'Receive important updates via email' },
          { key: 'paymentNotifications', name: 'Payment Notifications', description: 'Get notified about payment transactions' },
          { key: 'financingOffers', name: 'Financing Offers', description: 'Receive personalized financing opportunities' },
          { key: 'weeklyReports', name: 'Weekly Reports', description: 'Weekly business performance summaries' },
          { key: 'marketingInsights', name: 'Marketing Insights', description: 'Tips and insights to improve your marketing' }
        ].map((notification) => (
          <div key={notification.key} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h3 className="font-medium text-gray-900">{notification.name}</h3>
              <p className="text-sm text-gray-500">{notification.description}</p>
            </div>
            <button
              onClick={() => handleNotificationToggle(notification.key)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                notifications[notification.key] ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  notifications[notification.key] ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSecuritySection = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Security Settings</h2>
      
      <div className="space-y-4">
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-2">Password</h3>
          <p className="text-sm text-gray-500 mb-4">Last changed 30 days ago</p>
          <Button variant="secondary">Change Password</Button>
        </div>

        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-2">Two-Factor Authentication</h3>
          <p className="text-sm text-gray-500 mb-4">Add an extra layer of security to your account</p>
          <Button variant="secondary">Enable 2FA</Button>
        </div>

        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-2">API Keys</h3>
          <p className="text-sm text-gray-500 mb-4">Manage API keys for third-party integrations</p>
          <Button variant="secondary">Manage API Keys</Button>
        </div>
      </div>
    </div>
  );

  const renderBillingSection = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Billing & Subscription</h2>
      
      <div className="border border-gray-200 rounded-lg p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-medium text-gray-900">Current Plan</h3>
            <p className="text-2xl font-bold text-blue-600">Professional</p>
            <p className="text-sm text-gray-500">$99/month</p>
          </div>
          <Button variant="secondary">Upgrade Plan</Button>
        </div>
        
        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-900 mb-2">Plan Features</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>✓ Unlimited transactions</li>
            <li>✓ Advanced analytics</li>
            <li>✓ AI-powered insights</li>
            <li>✓ Priority support</li>
          </ul>
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg p-6">
        <h3 className="font-medium text-gray-900 mb-4">Payment Method</h3>
        <div className="flex items-center space-x-3">
          <div className="w-12 h-8 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">
            VISA
          </div>
          <div>
            <p className="text-sm text-gray-900">•••• •••• •••• 4242</p>
            <p className="text-xs text-gray-500">Expires 12/25</p>
          </div>
        </div>
        <Button variant="secondary" className="mt-4">Update Payment Method</Button>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case 'profile':
        return renderProfileSection();
      case 'integrations':
        return renderIntegrationsSection();
      case 'notifications':
        return renderNotificationsSection();
      case 'security':
        return renderSecuritySection();
      case 'billing':
        return renderBillingSection();
      default:
        return renderProfileSection();
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account and platform preferences</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:w-64 flex-shrink-0">
          <nav className="space-y-1">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors ${
                  activeSection === item.id
                    ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span className="mr-3 text-lg">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default Profile;