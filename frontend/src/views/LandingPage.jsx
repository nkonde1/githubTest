import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Navigation */}
            <nav className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center">
                            <div className="flex-shrink-0 flex items-center">
                                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-2">
                                    <span className="text-white font-bold text-xl">E</span>
                                </div>
                                <span className="text-xl font-bold text-gray-900">EasyFlow</span>
                            </div>
                        </div>
                        <div className="flex items-center space-x-4">
                            <Link to="/login" className="text-gray-500 hover:text-gray-900 font-medium">
                                Log in
                            </Link>
                            <Link
                                to="/signup"
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                            >
                                Start Free Trial
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <div className="flex-grow flex items-center justify-center bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 flex flex-col lg:flex-row items-center">
                    <div className="lg:w-1/2 lg:pr-12 mb-10 lg:mb-0">
                        <h1 className="text-4xl lg:text-5xl font-extrabold text-gray-900 leading-tight mb-6">
                            Financial Power for <br />
                            <span className="text-blue-600">Growth-Minded Businesses</span>
                        </h1>
                        <p className="text-xl text-gray-600 mb-8">
                            Manage payments, access financing, and get AI-powered insights.
                            All in one platform designed for small and medium businesses.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4">
                            <Link
                                to="/signup"
                                className="flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg shadow-lg hover:shadow-xl transition-all"
                            >
                                Start Free Monthly Trial
                            </Link>
                            <Link
                                to="/login"
                                className="flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg"
                            >
                                Log In
                            </Link>
                        </div>
                        <p className="mt-4 text-sm text-gray-500">
                            No credit card required for trial. Cancel anytime.
                        </p>
                    </div>
                    <div className="lg:w-1/2">
                        <div className="relative rounded-xl shadow-2xl overflow-hidden border border-gray-100 bg-gray-50 p-4">
                            {/* Abstract representation of the dashboard */}
                            <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
                                <div className="flex justify-between items-center border-b pb-4">
                                    <div className="h-6 w-32 bg-gray-200 rounded"></div>
                                    <div className="h-8 w-8 bg-blue-100 rounded-full"></div>
                                </div>
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="h-24 bg-blue-50 rounded p-4">
                                        <div className="h-4 w-12 bg-blue-200 rounded mb-2"></div>
                                        <div className="h-6 w-20 bg-blue-300 rounded"></div>
                                    </div>
                                    <div className="h-24 bg-green-50 rounded p-4">
                                        <div className="h-4 w-12 bg-green-200 rounded mb-2"></div>
                                        <div className="h-6 w-20 bg-green-300 rounded"></div>
                                    </div>
                                    <div className="h-24 bg-purple-50 rounded p-4">
                                        <div className="h-4 w-12 bg-purple-200 rounded mb-2"></div>
                                        <div className="h-6 w-20 bg-purple-300 rounded"></div>
                                    </div>
                                </div>
                                <div className="h-40 bg-gray-100 rounded"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Features Grid */}
            <div className="bg-gray-50 py-20">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold text-gray-900">Everything you need to grow</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
                            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-6">
                                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 mb-3">Seamless Payments</h3>
                            <p className="text-gray-600">Accept MTN and Airtel Mobile Money payments instantly. Track every transaction in real-time.</p>
                        </div>
                        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
                            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-6">
                                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 mb-3">Business Analytics</h3>
                            <p className="text-gray-600">Visualize your revenue, cash flow, and growth trends with our powerful analytics dashboard.</p>
                        </div>
                        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
                            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-6">
                                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 mb-3">Smart Financing</h3>
                            <p className="text-gray-600">Get access to business loans and credit lines tailored to your transaction history.</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="bg-white border-t border-gray-200 py-12">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-500">
                    <p>&copy; 2026 EasyFlow. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
