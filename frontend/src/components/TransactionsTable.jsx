import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchPaymentHistory } from '../redux/slices/financeSlice';
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

import BulkUploadModal from './Payments/BulkUploadModal';
import TelcoConnect from './Payments/TelcoConnect';

const TransactionsTable = () => {
    const dispatch = useDispatch();
    const { payments, totalPaymentsCount, loading, error } = useSelector((state) => state.finance.paymentHistory);
    const { token } = useSelector((state) => state.user);

    const [page, setPage] = useState(1);
    const [limit] = useState(10);
    const [status, setStatus] = useState('all');
    const [search, setSearch] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [showBulkUpload, setShowBulkUpload] = useState(false);
    const [showTelcoConnect, setShowTelcoConnect] = useState(false);

    // Debounce search input
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(search);
            setPage(1); // Reset to first page when search changes
        }, 500);

        return () => clearTimeout(timer);
    }, [search]);

    // Reset page when status filter changes
    useEffect(() => {
        setPage(1);
    }, [status]);

    // Fetch data when filters or page changes
    useEffect(() => {
        if (token) {
            dispatch(fetchPaymentHistory({
                page,
                limit,
                filters: {
                    status: status === 'all' ? undefined : status,
                    search: debouncedSearch
                }
            }));
        }
    }, [dispatch, page, limit, status, debouncedSearch, token]);

    const getStatusColor = (status) => {
        const colors = {
            completed: 'bg-emerald-100 text-emerald-800 border-emerald-200',
            pending: 'bg-amber-100 text-amber-800 border-amber-200',
            failed: 'bg-rose-100 text-rose-800 border-rose-200',
            processing: 'bg-blue-100 text-blue-800 border-blue-200',
            refunded: 'bg-purple-100 text-purple-800 border-purple-200',
        };
        return colors[status?.toLowerCase()] || 'bg-gray-100 text-gray-800 border-gray-200';
    };

    const getTypeColor = (type) => {
        const colors = {
            payment: 'bg-blue-50 text-blue-700',
            sale: 'bg-green-50 text-green-700',
            refund: 'bg-orange-50 text-orange-700',
            chargeback: 'bg-red-50 text-red-700',
        };
        return colors[type?.toLowerCase()] || 'bg-gray-50 text-gray-700';
    };

    const totalPages = Math.ceil(totalPaymentsCount / limit);

    return (
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
            {/* Header Section */}
            {/* Header Section */}
            <div className="bg-white px-8 py-6 flex justify-between items-center border-b border-gray-100">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Recent Transactions</h2>
                    <p className="text-gray-500">Manage and monitor your financial activity</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setShowTelcoConnect(true)}
                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg transition-all shadow-md hover:shadow-lg flex items-center gap-2"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <span>Import Mobile Money Transactions</span>
                    </button>
                </div>
            </div>

            {/* Filters Section */}
            <div className="bg-gray-50 border-b border-gray-200 px-8 py-5">
                <div className="flex flex-col lg:flex-row gap-4">
                    {/* Search Bar */}
                    <div className="flex-1 relative">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Search className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            type="text"
                            placeholder="Search by description or ID..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white"
                        />
                        {search && (
                            <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
                                <span className="text-xs text-gray-500">Searching...</span>
                            </div>
                        )}
                    </div>

                    {/* Status Filter */}
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Filter className="h-5 w-5 text-gray-400" />
                        </div>
                        <select
                            value={status}
                            onChange={(e) => setStatus(e.target.value)}
                            className="appearance-none pl-12 pr-10 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-white cursor-pointer min-w-[200px]"
                        >
                            <option value="all">All Status</option>
                            <option value="completed">Completed</option>
                            <option value="pending">Pending</option>
                            <option value="failed">Failed</option>
                            <option value="processing">Processing</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Table Section */}
            <div className="overflow-x-auto">
                <table className="w-full table-fixed">
                    <colgroup>
                        <col className="w-80" />
                        <col className="w-40" />
                        <col className="w-28" />
                        <col className="w-32" />
                        <col className="w-32" />
                        <col className="w-auto" />
                    </colgroup>
                    <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-300">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-r border-gray-200">
                                Transaction ID
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-r border-gray-200">
                                Date
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-r border-gray-200">
                                Type
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-r border-gray-200">
                                Status
                            </th>
                            <th className="px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider border-r border-gray-200">
                                Amount
                            </th>
                            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                Description
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr>
                                <td colSpan="6" className="px-8 py-12 text-center">
                                    <div className="flex justify-center items-center">
                                        <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent"></div>
                                    </div>
                                </td>
                            </tr>
                        ) : error ? (
                            <tr>
                                <td colSpan="6" className="px-8 py-12 text-center">
                                    <div className="text-red-600 font-medium">Error loading transactions</div>
                                    <div className="text-gray-500 text-sm mt-1">{error}</div>
                                </td>
                            </tr>
                        ) : payments && payments.length > 0 ? (
                            payments.map((transaction, index) => (
                                <tr
                                    key={transaction.id}
                                    className={`
                                        ${index % 2 === 0 ? 'bg-white' : 'bg-gradient-to-r from-blue-50/30 to-indigo-50/30'}
                                        hover:bg-gradient-to-r hover:from-blue-100/50 hover:to-indigo-100/50
                                        transition-all duration-200 
                                        border-b border-gray-200
                                        group
                                    `}
                                    style={{
                                        animation: `fadeIn 0.3s ease-in-out ${index * 0.05}s backwards`
                                    }}
                                >
                                    <td className="px-6 py-5 border-r border-gray-100">
                                        <div
                                            className="text-xs font-mono font-medium text-gray-900 group-hover:text-blue-600 transition-colors cursor-pointer break-all"
                                            onClick={() => {
                                                navigator.clipboard.writeText(transaction.id);
                                                // Could add toast notification here
                                            }}
                                            title="Click to copy"
                                        >
                                            {transaction.id}
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 whitespace-nowrap border-r border-gray-100">
                                        <div className="text-sm font-medium text-gray-900">
                                            {new Date(transaction.created_at).toLocaleDateString('en-US', {
                                                month: 'short',
                                                day: 'numeric',
                                                year: 'numeric'
                                            })}
                                        </div>
                                        <div className="text-xs text-gray-500 mt-0.5">
                                            {new Date(transaction.created_at).toLocaleTimeString('en-US', {
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 whitespace-nowrap border-r border-gray-100">
                                        <span className={`inline-flex px-3 py-1 rounded-lg text-xs font-bold ${getTypeColor(transaction.transaction_type)}`}>
                                            {transaction.transaction_type || 'N/A'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-5 whitespace-nowrap border-r border-gray-100">
                                        <span className={`inline-flex px-3 py-1 rounded-lg text-xs font-bold border-2 ${getStatusColor(transaction.status)}`}>
                                            {transaction.status || 'N/A'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-5 whitespace-nowrap text-right border-r border-gray-100">
                                        <div className="text-sm font-bold text-gray-900">
                                            {transaction.currency || '$'} {Number(transaction.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="text-sm text-gray-700 max-w-md truncate">
                                            {transaction.description || 'No description'}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr className="bg-white">
                                <td colSpan="6" className="px-8 py-12 text-center">
                                    <div className="text-gray-500">
                                        <div className="text-lg font-medium mb-1">No transactions found</div>
                                        <div className="text-sm">
                                            {search || status !== 'all'
                                                ? 'Try adjusting your filters'
                                                : 'Showing 0 to 0 of 0 results'}
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination Section */}
            <div className="bg-gray-50 border-t border-gray-200 px-8 py-5">
                <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-700">
                        Showing <span className="font-semibold">{payments && payments.length > 0 ? (page - 1) * limit + 1 : 0}</span> to{' '}
                        <span className="font-semibold">{Math.min(page * limit, totalPaymentsCount)}</span> of{' '}
                        <span className="font-semibold">{totalPaymentsCount}</span> results
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage(page - 1)}
                            disabled={page === 1}
                            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-md"
                        >
                            <ChevronLeft className="h-4 w-4 mr-1" />
                            Previous
                        </button>
                        <div className="flex items-center gap-1">
                            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                                const pageNum = i + 1;
                                return (
                                    <button
                                        key={pageNum}
                                        onClick={() => setPage(pageNum)}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${page === pageNum
                                            ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                                            }`}
                                    >
                                        {pageNum}
                                    </button>
                                );
                            })}
                        </div>
                        <button
                            onClick={() => setPage(page + 1)}
                            disabled={page === totalPages}
                            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-md"
                        >
                            Next
                            <ChevronRight className="h-4 w-4 ml-1" />
                        </button>
                    </div>
                </div>
            </div>

            <style>{`
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            `}</style>

            {/* Bulk Upload Modal */}
            <BulkUploadModal
                isOpen={showBulkUpload}
                onClose={() => setShowBulkUpload(false)}
                onUploadSuccess={() => {
                    // Trigger refresh
                    if (token) {
                        dispatch(fetchPaymentHistory({
                            page,
                            limit,
                            filters: {
                                status: status === 'all' ? undefined : status,
                                search: debouncedSearch
                            }
                        }));
                    }
                }}
            />

            {/* Telco Connect Modal */}
            <TelcoConnect
                isOpen={showTelcoConnect}
                onClose={() => setShowTelcoConnect(false)}
                onImportSuccess={() => {
                    if (token) {
                        dispatch(fetchPaymentHistory({
                            page,
                            limit,
                            filters: {
                                status: status === 'all' ? undefined : status,
                                search: debouncedSearch
                            }
                        }));
                    }
                }}
            />
        </div>
    );
};

export default TransactionsTable;
