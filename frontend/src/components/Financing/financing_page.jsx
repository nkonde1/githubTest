import React, { useEffect, useState, useCallback } from 'react';
import api from '../../services/api'; // adjust path if needed
import { RefreshCw } from 'lucide-react';
import { financingService } from '../../services/financingService';

const FinancingPage = () => {
    const [metrics, setMetrics] = useState(null);
    const [creditScoreData, setCreditScoreData] = useState(null);
    const [loanOffers, setLoanOffers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const METRICS_ENDPOINT = '/api/v1/metrics/business_metrics';

    useEffect(() => {
        let mounted = true;
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                // 1. Fetch Metrics
                const metricsRes = await api.get(METRICS_ENDPOINT);
                const metricsPayload = Array.isArray(metricsRes.data) ? metricsRes.data : [metricsRes.data];

                // 2. Fetch Credit Score
                const scoreData = await financingService.getCreditScore();

                // 3. Fetch Loan Offers (using the score we just got)
                const offersData = await financingService.getFinancingOffers(scoreData.score);

                if (!mounted) return;

                setMetrics(metricsPayload);
                setCreditScoreData(scoreData);
                setLoanOffers(offersData.offers || []);

            } catch (err) {
                console.error('FinancingPage: fetch data failed', err);
                if (mounted) setError(err);
            } finally {
                if (mounted) setLoading(false);
            }
        };

        fetchData();
        return () => { mounted = false; };
    }, []);

    const handleRefresh = useCallback(async () => {
        setLoading(true);
        try {
            await api.post('/api/v1/metrics/business_metrics/update');
            // Re-fetch data
            const metricsRes = await api.get(METRICS_ENDPOINT);
            const metricsPayload = Array.isArray(metricsRes.data) ? metricsRes.data : [metricsRes.data];
            const scoreData = await financingService.getCreditScore();
            const offersData = await financingService.getFinancingOffers(scoreData.score);

            setMetrics(metricsPayload);
            setCreditScoreData(scoreData);
            setLoanOffers(offersData.offers || []);
        } catch (err) {
            console.error('Refresh failed', err);
            setError(err);
        } finally {
            setLoading(false);
        }
    }, []);

    if (loading) return <div className="p-6">Loading financing data...</div>;
    if (error) return <div className="p-6 text-red-600">Error loading financing data.</div>;

    const latest = metrics && metrics.length > 0 ? metrics[0] : {};
    const fmt = (v) => (v === null || v === undefined ? '—' : Number(v).toLocaleString());

    // Credit Score Color
    const getScoreColor = (score) => {
        if (score >= 750) return 'text-green-600';
        if (score >= 650) return 'text-blue-600';
        if (score >= 550) return 'text-yellow-600';
        return 'text-red-600';
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-blue-50 p-8">
            {/* Header */}
            <div className="mb-8">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-5xl font-bold text-gray-900">Financing</h1>
                        <p className="text-gray-600 mt-2">Access credit scores and financing options</p>
                    </div>
                    <button
                        onClick={handleRefresh}
                        disabled={loading}
                        className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50"
                    >
                        <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
                        <span>{loading ? 'Refreshing...' : 'Refresh'}</span>
                    </button>
                </div>
            </div>

            {/* Top Section: Credit Score & Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">

                {/* Credit Score Card */}
                <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100 md:col-span-1 flex flex-col items-center justify-center">
                    <h2 className="text-lg font-semibold text-gray-600 mb-2">Business Credit Score</h2>
                    <div className={`text-5xl font-bold mb-2 ${getScoreColor(creditScoreData?.score)}`}>
                        {creditScoreData?.score || '—'}
                    </div>
                    <div className="text-sm font-medium text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                        Rating: {creditScoreData?.rating || 'Unknown'}
                    </div>
                    <div className="mt-4 text-xs text-gray-400 text-center">
                        Calculated based on revenue, cash flow, and transaction history.
                    </div>
                </div>

                {/* Key Metrics Cards */}
                <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="text-sm text-gray-500 mb-1">Monthly Revenue</div>
                        <div className="text-2xl font-bold text-gray-800">
                            {latest.monthly_revenue
                                ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'ZMW' }).format(latest.monthly_revenue * 27.0)
                                : '—'}
                        </div>
                        <div className="text-xs text-green-600 mt-2">Updated recently</div>
                    </div>
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="text-sm text-gray-500 mb-1">Cash Flow</div>
                        <div className="text-2xl font-bold text-gray-800">
                            {latest.cash_flow
                                ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'ZMW' }).format(latest.cash_flow * 27.0)
                                : '—'}
                        </div>
                        <div className="text-xs text-gray-400 mt-2">Last 30 days</div>
                    </div>
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="text-sm text-gray-500 mb-1">Profit Margin</div>
                        <div className="text-2xl font-bold text-gray-800">{latest.profit_margin ? `${(Number(latest.profit_margin) * 100).toFixed(1)}%` : '—'}</div>
                    </div>
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="text-sm text-gray-500 mb-1">Transaction Volume (90d)</div>
                        <div className="text-2xl font-bold text-gray-800">
                            {creditScoreData?.factors?.transaction_volume_90d
                                ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'ZMW' }).format(creditScoreData.factors.transaction_volume_90d * 27.0)
                                : '—'}
                        </div>
                    </div>
                </div>
            </div>

            {/* Loan Offers Section */}
            <div className="mb-8">
                <h2 className="text-2xl font-bold mb-4 text-gray-800">Available Loan Offers</h2>
                <p className="text-gray-600 mb-6">Based on your credit score of {creditScoreData?.score}, you are eligible for the following financing options.</p>

                {loanOffers.length === 0 ? (
                    <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg text-yellow-800">
                        No specific loan offers available at this time. Improve your credit score to unlock more options.
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {loanOffers.map((offer, index) => (
                            <div key={index} className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow">
                                <div className="p-6">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center">
                                            <img src={offer.logo_url} alt={offer.provider} className="w-12 h-12 rounded-full mr-4 bg-gray-100" />
                                            <div>
                                                <h3 className="font-bold text-lg text-gray-900">{offer.provider}</h3>
                                                <div className="text-sm text-gray-500">{offer.loan_name}</div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-2xl font-bold text-blue-600">{offer.interest_rate}%</div>
                                            <div className="text-xs text-gray-500">Interest Rate</div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 mb-4">
                                        <div className="bg-gray-50 p-3 rounded-lg">
                                            <div className="text-xs text-gray-500">Amount</div>
                                            <div className="font-semibold text-gray-800">ZMW {fmt(offer.amount_range.min * 28.0)} - ZMW {fmt(offer.amount_range.max * 28.0)}</div>
                                        </div>
                                        <div className="bg-gray-50 p-3 rounded-lg">
                                            <div className="text-xs text-gray-500">Term</div>
                                            <div className="font-semibold text-gray-800">{offer.term_months.join(', ')} months</div>
                                        </div>
                                    </div>

                                    <div className="mb-6">
                                        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Requirements</div>
                                        <div className="flex flex-wrap gap-2">
                                            {offer.requirements.map((req, i) => (
                                                <span key={i} className="px-2 py-1 bg-green-50 text-green-700 text-xs rounded-md border border-green-100">
                                                    {req}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <button
                                        className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
                                        onClick={() => window.open(`https://example.com/apply?provider=${encodeURIComponent(offer.provider)}`, '_blank')}
                                    >
                                        Apply Now
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Detailed Metrics Table (kept from original but styled better) */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                    <h3 className="font-semibold text-gray-700">Detailed Business Metrics</h3>
                </div>
                <div className="p-6">
                    <table className="w-full text-left">
                        <tbody>
                            <tr className="border-b border-gray-50"><td className="py-3 text-gray-500">Customer count</td><td className="py-3 font-medium">{fmt(latest.customer_count)}</td></tr>
                            <tr className="border-b border-gray-50"><td className="py-3 text-gray-500">Avg order value</td><td className="py-3 font-medium">{latest.avg_order_value ? `ZMW ${fmt(latest.avg_order_value * 27.0)}` : '—'}</td></tr>
                            <tr className="border-b border-gray-50"><td className="py-3 text-gray-500">Repeat customer rate</td><td className="py-3 font-medium">{latest.repeat_customer_rate ? `${(Number(latest.repeat_customer_rate) * 100).toFixed(1)}%` : '—'}</td></tr>
                            <tr className="border-b border-gray-50"><td className="py-3 text-gray-500">Inventory turnover</td><td className="py-3 font-medium">{latest.inventory_turnover ?? '—'}</td></tr>
                            <tr><td className="py-3 text-gray-500">Chargeback rate</td><td className="py-3 font-medium">{latest.chargeback_rate ? `${(Number(latest.chargeback_rate) * 100).toFixed(2)}%` : '—'}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default FinancingPage;