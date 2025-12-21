import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchInsights, fetchRecommendations, clearInsights } from '../state/actions';
import { LoadingSpinner, LoadingCard } from '../components/Loading';
import Chart from '../components/Chart';

const InsightsPage = () => {
  const dispatch = useDispatch();
  const { insights, recommendations, loading, error } = useSelector(state => state.insights);
  const [selectedTimeframe, setSelectedTimeframe] = useState('7d');
  const [activeTab, setActiveTab] = useState('overview');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  useEffect(() => {
    dispatch(fetchInsights(selectedTimeframe));
    dispatch(fetchRecommendations());
  }, [dispatch, selectedTimeframe]);

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = { role: 'user', content: chatInput, timestamp: new Date() };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      // Simulate AI response - replace with actual API call
      setTimeout(() => {
        const aiResponse = {
          role: 'assistant',
          content: `Based on your data, here's what I found regarding "${chatInput}": Your revenue has increased by 15% this month, with your top-performing product category being electronics. I recommend focusing your marketing budget on social media ads, as they're showing a 3.2x ROI compared to other channels.`,
          timestamp: new Date()
        };
        setChatMessages(prev => [...prev, aiResponse]);
        setIsChatLoading(false);
      }, 2000);
    } catch (error) {
      setIsChatLoading(false);
      console.error('Chat error:', error);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'recommendations', label: 'Recommendations', icon: '💡' },
    { id: 'predictions', label: 'Predictions', icon: '🔮' },
    { id: 'chat', label: 'AI Assistant', icon: '🤖' }
  ];

  const timeframes = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
    { value: '1y', label: 'Last Year' }
  ];

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Key Insights Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          Array.from({ length: 3 }).map((_, index) => (
            <LoadingCard key={index} height="160px" />
          ))
        ) : (
          insights?.keyMetrics?.map((metric, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{metric.title}</h3>
                <span className="text-2xl">{metric.icon}</span>
              </div>
              <div className="mb-2">
                <span className="text-3xl font-bold text-gray-900">{metric.value}</span>
                <span className="text-sm text-gray-500 ml-2">{metric.unit}</span>
              </div>
              <div className="flex items-center">
                <span className={`text-sm font-medium ${
                  metric.change > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {metric.change > 0 ? '↗' : '↘'} {Math.abs(metric.change)}%
                </span>
                <span className="text-sm text-gray-500 ml-2">vs last period</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Insights Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Trends</h3>
        {loading ? (
          <div className="h-80 bg-gray-100 rounded animate-pulse"></div>
        ) : (
          <Chart
            type="line"
            data={insights?.chartData || []}
            height={320}
            options={{
              responsive: true,
              plugins: {
                legend: { position: 'top' },
                title: { display: false }
              }
            }}
          />
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { title: 'Optimize Ad Spend', action: 'View Details', color: 'blue' },
            { title: 'Inventory Reorder', action: 'Schedule', color: 'green' },
            { title: 'Cash Flow Alert', action: 'Review', color: 'yellow' },
            { title: 'Customer Retention', action: 'Improve', color: 'purple' }
          ].map((item, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <h4 className="font-medium text-gray-900 mb-2">{item.title}</h4>
              <button className={`w-full px-4 py-2 rounded-md text-sm font-medium bg-${item.color}-100 text-${item.color}-700 hover:bg-${item.color}-200`}>
                {item.action}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderRecommendations = () => (
    <div className="space-y-6">
      {loading ? (
        Array.from({ length: 4 }).map((_, index) => (
          <LoadingCard key={index} height="180px" />
        ))
      ) : (
        recommendations?.map((rec, index) => (
          <div key={index} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  rec.priority === 'high' ? 'bg-red-100 text-red-600' :
                  rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                  'bg-green-100 text-green-600'
                }`}>
                  {rec.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{rec.title}</h3>
                  <p className="text-sm text-gray-500">{rec.category}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                rec.priority === 'high' ? 'bg-red-100 text-red-700' :
                rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                'bg-green-100 text-green-700'
              }`}>
                {rec.priority} priority
              </span>
            </div>
            
            <p className="text-gray-700 mb-4">{rec.description}</p>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500">
                  Potential Impact: <span className="font-medium text-green-600">{rec.impact}</span>
                </span>
                <span className="text-sm text-gray-500">
                  Effort: <span className="font-medium">{rec.effort}</span>
                </span>
              </div>
              <div className="flex space-x-2">
                <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
                  Learn More
                </button>
                <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
                  Implement
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );

  const renderPredictions = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Forecast</h3>
        {loading ? (
          <div className="h-64 bg-gray-100 rounded animate-pulse"></div>
        ) : (
          <Chart
            type="line"
            data={insights?.forecastData || []}
            height={256}
            options={{
              responsive: true,
              plugins: {
                legend: { position: 'top' },
                title: { display: false }
              }
            }}
          />
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cash Flow Prediction</h3>
          <div className="space-y-4">
            {[
              { period: 'Next 30 days', amount: '+$45,200', confidence: '85%', trend: 'up' },
              { period: 'Next 60 days', amount: '+$78,900', confidence: '78%', trend: 'up' },
              { period: 'Next 90 days', amount: '+$112,400', confidence: '72%', trend: 'up' }
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{item.period}</p>
                  <p className="text-sm text-gray-500">Confidence: {item.confidence}</p>
                </div>
                <div className="text-right">
                  <p className={`font-semibold ${item.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                    {item.amount}
                  </p>
                  <span className="text-sm text-gray-500">
                    {item.trend === 'up' ? '↗' : '↘'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Inventory Alerts</h3>
          <div className="space-y-4">
            {[
              { product: 'iPhone 15 Cases', status: 'Low Stock', days: '5 days', severity: 'high' },
              { product: 'Wireless Chargers', status: 'Reorder Soon', days: '12 days', severity: 'medium' },
              { product: 'Screen Protectors', status: 'Optimal', days: '28 days', severity: 'low' }
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{item.product}</p>
                  <p className="text-sm text-gray-500">{item.status}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{item.days}</p>
                  <span className={`inline-block w-2 h-2 rounded-full ${
                    item.severity === 'high' ? 'bg-red-500' :
                    item.severity === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                  }`}></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderChat = () => (
    <div className="bg-white rounded-lg shadow-md h-96 flex flex-col">
      <div className="flex-1 p-6 overflow-y-auto">
        {chatMessages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-4xl mb-4">🤖</div>
            <p className="text-lg font-medium mb-2">AI Assistant Ready</p>
            <p className="text-sm">Ask me anything about your business data, performance, or get recommendations.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {chatMessages.map((message, index) => (
              <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.role === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  <p className="text-sm">{message.content}</p>
                  <p className="text-xs opacity-75 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            {isChatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <LoadingSpinner size="sm" />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      
      <form onSubmit={handleChatSubmit} className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask about your business performance..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isChatLoading}
          />
          <button
            type="submit"
            disabled={isChatLoading || !chatInput.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Insights</h1>
              <p className="mt-2 text-gray-600">
                Get intelligent recommendations and predictions for your business
              </p>
            </div>
            
            <div className="mt-4 sm:mt-0">
              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {timeframes.map((timeframe) => (
                  <option key={timeframe.value} value={timeframe.value}>
                    {timeframe.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-red-600 mr-2">⚠️</span>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'recommendations' && renderRecommendations()}
          {activeTab === 'predictions' && renderPredictions()}
          {activeTab === 'chat' && renderChat()}
        </div>
      </div>
    </div>
  );
};

export default InsightsPage;