
import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { useAuth } from '../../contexts/AuthContext';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  HomeIcon,
  CreditCardIcon,
  ChartBarIcon,
  BanknotesIcon,
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  UserCircleIcon,
  BellIcon,
  MagnifyingGlassIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';

/**
 * Main Layout Component
 * Provides the overall structure for the finance platform with:
 * - Collapsible sidebar navigation
 * - Header with user info and notifications
 * - Main content area with protected routes
 * - Responsive design for mobile/desktop
 */
const Layout = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user, logout } = useAuth();
  
  // Redux state for real-time data
  const { 
    totalBalance, 
    pendingTransactions, 
    monthlyRevenue 
  } = useSelector(state => state.finance || {});
  
  const { 
    alertCount, 
    isLoading: analyticsLoading 
  } = useSelector(state => state.analytics || {});

  // Navigation items configuration
  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
      current: location.pathname === '/dashboard'
    },
    {
      name: 'Payments',
      href: '/payments',
      icon: CreditCardIcon,
      current: location.pathname.startsWith('/payments'),
      badge: pendingTransactions > 0 ? pendingTransactions : null
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: ChartBarIcon,
      current: location.pathname.startsWith('/analytics'),
      badge: alertCount > 0 ? alertCount : null
    },
    {
      name: 'Financing',
      href: '/financing',
      icon: BanknotesIcon,
      current: location.pathname.startsWith('/financing')
    },
    {
      name: 'AI Assistant',
      href: '/ai-chat',
      icon: ChatBubbleLeftRightIcon,
      current: location.pathname.startsWith('/ai-chat')
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Cog6ToothIcon,
      current: location.pathname.startsWith('/settings')
    }
  ];

  // Handle responsive sidebar
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarCollapsed(true);
        setMobileMenuOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial check

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch notifications on mount
  useEffect(() => {
    // Simulate fetching notifications
    const mockNotifications = [
      { id: 1, message: 'Payment processing completed', type: 'success', time: '2 min ago' },
      { id: 2, message: 'New financing offer available', type: 'info', time: '1 hour ago' }
    ];
    setNotifications(mockNotifications);
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <div className="layout-shell">
      {/* Sidebar */}
      <aside className={`layout-sidebar ${sidebarCollapsed ? 'collapsed' : ''} ${mobileMenuOpen ? 'open' : ''}`}>
        <div className="sidebar-head">
          {!sidebarCollapsed && (
            <div className="brand">
              <div className="logo">Easy</div>
              <span className="title">EasyFlow</span>
            </div>
          )}
          <button onClick={toggleSidebar} className="icon-btn" aria-label="Toggle sidebar">
            {sidebarCollapsed ? (
              <ChevronRightIcon width={20} height={20} />
            ) : (
              <ChevronLeftIcon width={20} height={20} />
            )}
          </button>
        </div>

        <nav className="sidebar-nav">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.name}
                onClick={() => {
                  navigate(item.href);
                  setMobileMenuOpen(false);
                }}
                className={`nav-link ${item.current ? 'active' : ''}`}
              >
                <Icon width={20} height={20} className={sidebarCollapsed ? 'icon-centered' : 'icon-spaced'} />
                {!sidebarCollapsed && (
                  <>
                    <span className="label">{item.name}</span>
                    {item.badge && <span className="badge">{item.badge}</span>}
                  </>
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-user">
          {!sidebarCollapsed ? (
            <div className="user-box">
              <div className="avatar"><UserCircleIcon width={24} height={24} /></div>
              <div className="user-meta">
                <p className="name">{user?.name || 'User'}</p>
                <p className="email">{user?.email || 'demo@financeai.com'}</p>
              </div>
            </div>
          ) : (
            <div className="user-icon">
              <UserCircleIcon width={24} height={24} />
            </div>
          )}
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileMenuOpen && <div className="mobile-overlay" onClick={() => setMobileMenuOpen(false)} />}

      {/* Main Content Area */}
      <div className="layout-content">
        <header className="layout-header">
          <button className="menu-btn" onClick={toggleMobileMenu} aria-label="Open menu">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
          <h1 className="page-title">{location.pathname.split('/')[1] || 'Dashboard'}</h1>
          <div className="header-actions">
            <div className="search">
              <MagnifyingGlassIcon width={16} height={16} className="search-icon" />
              <input type="text" placeholder="Search..." />
            </div>
            <button className="icon-btn">
              <BellIcon width={20} height={20} />
              {notifications.length > 0 && <span className="dot">{notifications.length}</span>}
            </button>
            <button className="btn ghost" onClick={handleLogout}>
              <ArrowRightOnRectangleIcon width={18} height={18} />
              <span className="hide-sm">Logout</span>
            </button>
          </div>
        </header>

        <main className="layout-main">
          {analyticsLoading && (
            <div className="notice info">Loading analytics data...</div>
          )}
          <div className="container">
            <Outlet />
          </div>
        </main>

        <footer className="layout-footer">
          <div className="container footer-inner">
            <p>© 2025 EasyFlow. All rights reserved.</p>
            <div className="links">
              <button className="link">Privacy</button>
              <button className="link">Terms</button>
              <button className="link">Support</button>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Layout;