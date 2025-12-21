import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user } = useSelector(state => state.auth);
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const sidebarItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: '🏠',
      path: '/dashboard',
      children: []
    },
    {
      id: 'payments',
      label: 'Payments',
      icon: '💳',
      path: '/payments',
      children: [
        { label: 'Transactions', path: '/payments/transactions' },
        { label: 'Payment Methods', path: '/payments/methods' },
        { label: 'Reconciliation', path: '/payments/reconciliation' }
      ]
    },
    {
      id: 'financing',
      label: 'Financing',
      icon: '💰',
      path: '/financing',
      children: [
        { label: 'Available Offers', path: '/financing/offers' },
        { label: 'Active Loans', path: '/financing/active' },
        { label: 'Payment History', path: '/financing/history' }
      ]
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: '📈',
      path: '/analytics',
      children: [
        { label: 'Performance', path: '/analytics/performance' },
        { label: 'Profitability', path: '/analytics/profitability' },
        { label: 'Customer Insights', path: '/analytics/customers' },
        { label: 'Inventory Analysis', path: '/analytics/inventory' }
      ]
    },
    {
      id: 'insights',
      label: 'AI Insights',
      icon: '🤖',
      path: '/insights',
      children: [
        { label: 'Recommendations', path: '/insights/recommendations' },
        { label: 'Predictions', path: '/insights/predictions' },
        { label: 'Chat Assistant', path: '/insights/chat' }
      ]
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: '⚙️',
      path: '/settings',
      children: [
        { label: 'Account', path: '/settings/account' },
        { label: 'Integrations', path: '/settings/integrations' },
        { label: 'Notifications', path: '/settings/notifications' },
        { label: 'Security', path: '/settings/security' }
      ]
    }
  ];

  const isActivePath = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed left-0 top-16 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out z-50
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:z-auto
      `}>
        <div className="flex flex-col h-full">
          {/* User Info */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold">
                  {user?.name?.charAt(0) || 'U'}
                </span>
              </div>
              <div>
                <p className="font-medium text-gray-900">{user?.name || 'User'}</p>
                <p className="text-sm text-gray-500">{user?.email}</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4">
            <ul className="space-y-2">
              {sidebarItems.map((item) => (
                <li key={item.id}>
                  {item.children.length > 0 ? (
                    <>
                      <button
                        onClick={() => toggleSection(item.id)}
                        className={`
                          w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors
                          ${isActivePath(item.path) 
                            ? 'bg-blue-100 text-blue-700' 
                            : 'text-gray-700 hover:bg-gray-100'
                          }
                        `}
                      >
                        <div className="flex items-center space-x-3">
                          <span className="text-lg">{item.icon}</span>
                          <span className="font-medium">{item.label}</span>
                        </div>
                        <svg 
                          className={`w-4 h-4 transition-transform ${
                            expandedSections[item.id] ? 'rotate-90' : ''
                          }`}
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                      
                      {expandedSections[item.id] && (
                        <ul className="mt-2 ml-6 space-y-1">
                          {item.children.map((child) => (
                            <li key={child.path}>
                              <Link
                                to={child.path}
                                className={`
                                  block px-3 py-2 rounded-md text-sm transition-colors
                                  ${isActivePath(child.path)
                                    ? 'bg-blue-50 text-blue-600 border-l-2 border-blue-500'
                                    : 'text-gray-600 hover:bg-gray-100'
                                  }
                                `}
                                onClick={onClose}
                              >
                                {child.label}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      )}
                    </>
                  ) : (
                    <Link
                      to={item.path}
                      className={`
                        flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors
                        ${isActivePath(item.path)
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100'
                        }
                      `}
                      onClick={onClose}
                    >
                      <span className="text-lg">{item.icon}</span>
                      <span className="font-medium">{item.label}</span>
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500 text-center">
              <p>EasyFlow v1.0</p>
              <p>© 2025 All rights reserved</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;