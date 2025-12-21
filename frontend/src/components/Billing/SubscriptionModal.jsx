import React, { useState } from 'react';
import api from '../../services/api';

const SubscriptionModal = ({ isOpen, onClose, onSuccess }) => {
    const [step, setStep] = useState(1); // 1: Select Plan, 2: Payment Details, 3: Success, 4: Pending
    const [selectedPlan, setSelectedPlan] = useState('6_months');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [provider, setProvider] = useState('mtn');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [transactionId, setTransactionId] = useState(null);

    if (!isOpen) return null;

    const plans = {
        '6_months': { name: '6 Months Plan', price: 2500, label: 'ZMW 2,500' },
        '12_months': { name: '12 Months Plan', price: 4500, label: 'ZMW 4,500 (Save 10%)' }
    };

    const pollStatus = async (txId) => {
        const maxAttempts = 24; // 2 minutes (5s interval)
        let attempts = 0;

        const check = async () => {
            try {
                const response = await api.get(`/api/v1/billing/check-status/${txId}`);
                if (response.data.status === 'successful') {
                    setLoading(false);
                    setStep(3);
                    if (onSuccess) onSuccess();
                } else if (response.data.status === 'failed') {
                    setLoading(false);
                    setError('Payment failed. Please try again.');
                    setStep(2);
                } else {
                    attempts++;
                    if (attempts < maxAttempts) {
                        setTimeout(check, 5000);
                    } else {
                        setLoading(false);
                        setError('Payment confirmation timed out. Please check your phone or try again.');
                        setStep(2);
                    }
                }
            } catch (err) {
                console.error("Polling error", err);
                // Continue polling on error? Maybe not.
                setLoading(false);
                setError('Error checking payment status.');
                setStep(2);
            }
        };

        check();
    };

    const handlePayment = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await api.post('/api/v1/billing/subscribe', {
                plan_id: selectedPlan,
                phone_number: phoneNumber,
                provider: provider
            });

            const { status, transaction_id } = response.data;

            if (status === 'successful') {
                setLoading(false);
                setStep(3);
                if (onSuccess) onSuccess();
            } else if (status === 'pending' || status === 'initiated') {
                setTransactionId(transaction_id);
                setStep(4); // Move to pending UI
                pollStatus(transaction_id);
            } else {
                setLoading(false);
                setError('Payment failed.');
            }

        } catch (err) {
            setLoading(false);
            setError(err.response?.data?.detail || 'Payment failed. Please try again.');
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden">
                <div className="p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold text-gray-900">
                            {step === 3 ? 'Payment Successful' : step === 4 ? 'Confirm Payment' : 'Upgrade Subscription'}
                        </h2>
                        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {step === 1 && (
                        <div className="space-y-4">
                            <p className="text-gray-600 mb-4">Select a billing cycle for your subscription.</p>

                            {Object.entries(plans).map(([id, plan]) => (
                                <div
                                    key={id}
                                    onClick={() => setSelectedPlan(id)}
                                    className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${selectedPlan === id ? 'border-blue-600 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                                        }`}
                                >
                                    <div className="flex justify-between items-center">
                                        <span className="font-semibold text-gray-900">{plan.name}</span>
                                        <span className="font-bold text-blue-600">{plan.label}</span>
                                    </div>
                                </div>
                            ))}

                            <button
                                onClick={() => setStep(2)}
                                className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700"
                            >
                                Continue
                            </button>
                        </div>
                    )}

                    {step === 2 && (
                        <form onSubmit={handlePayment} className="space-y-4">
                            <p className="text-gray-600 mb-4">Enter your mobile money details.</p>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                                <div className="grid grid-cols-2 gap-4">
                                    <button
                                        type="button"
                                        onClick={() => setProvider('mtn')}
                                        className={`p-3 border rounded-lg flex items-center justify-center font-medium ${provider === 'mtn' ? 'bg-yellow-100 border-yellow-400 text-yellow-800' : 'border-gray-200'
                                            }`}
                                    >
                                        MTN MoMo
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setProvider('airtel')}
                                        className={`p-3 border rounded-lg flex items-center justify-center font-medium ${provider === 'airtel' ? 'bg-red-100 border-red-400 text-red-800' : 'border-gray-200'
                                            }`}
                                    >
                                        Airtel Money
                                    </button>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                                <input
                                    type="tel"
                                    required
                                    placeholder="e.g., 096xxxxxxx"
                                    value={phoneNumber}
                                    onChange={(e) => setPhoneNumber(e.target.value)}
                                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                />
                            </div>

                            <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-gray-600">Plan</span>
                                    <span className="font-medium">{plans[selectedPlan].name}</span>
                                </div>
                                <div className="flex justify-between text-lg font-bold">
                                    <span>Total</span>
                                    <span>{plans[selectedPlan].label}</span>
                                </div>
                            </div>

                            {error && <p className="text-red-600 text-sm">{error}</p>}

                            <div className="flex gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setStep(1)}
                                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                                >
                                    Back
                                </button>
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="flex-1 bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {loading ? 'Processing...' : 'Pay Now'}
                                </button>
                            </div>
                        </form>
                    )}

                    {step === 4 && (
                        <div className="text-center py-6">
                            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
                                <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-bold text-gray-900 mb-2">Payment Pending</h3>
                            <p className="text-gray-600 mb-6">Please check your phone ({phoneNumber}) and approve the payment request from {provider === 'mtn' ? 'MTN MoMo' : 'Airtel Money'}.</p>
                            <div className="flex justify-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="text-center py-6">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-bold text-gray-900 mb-2">Payment Successful!</h3>
                            <p className="text-gray-600 mb-6">Your subscription has been activated.</p>
                            <button
                                onClick={onClose}
                                className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700"
                            >
                                Done
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SubscriptionModal;
