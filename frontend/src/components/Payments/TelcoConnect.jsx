import React, { useState } from 'react';
import { X, Smartphone, ShieldCheck, Download, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import telcoService from '../../services/telcoService';

const TelcoConnect = ({ isOpen, onClose, onImportSuccess }) => {
    const [step, setStep] = useState(1); // 1: Connect, 2: Verify, 3: Pull, 4: Success
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Form Data
    const [provider, setProvider] = useState('MTN');
    const [walletNumber, setWalletNumber] = useState('');
    const [otp, setOtp] = useState('');
    const [connectId, setConnectId] = useState(null);
    const [dateRange, setDateRange] = useState({
        from: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
        to: new Date().toISOString().split('T')[0]
    });
    const [results, setResults] = useState(null);

    if (!isOpen) return null;

    const handleConnect = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await telcoService.connect({ provider, wallet_number: walletNumber });
            setConnectId(res.connect_id);
            setStep(2);
        } catch (err) {
            setError(err.response?.data?.detail || 'Connection failed');
        } finally {
            setLoading(false);
        }
    };

    const handleVerify = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await telcoService.verify({ connect_id: connectId, otp });
            setStep(3);
        } catch (err) {
            setError(err.response?.data?.detail || 'Verification failed');
        } finally {
            setLoading(false);
        }
    };

    const handlePull = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await telcoService.pull({
                provider,
                from_date: dateRange.from,
                to_date: dateRange.to
            });
            setResults(res);
            setStep(4);
            if (onImportSuccess) onImportSuccess();
        } catch (err) {
            setError(err.response?.data?.detail || 'Data pull failed');
        } finally {
            setLoading(false);
        }
    };

    const reset = () => {
        setStep(1);
        setWalletNumber('');
        setOtp('');
        setConnectId(null);
        setResults(null);
        setError(null);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl max-w-md w-full mx-4 overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="bg-gray-50 px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <Smartphone className="h-5 w-5 text-blue-600" />
                        Connect Telco Account
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6">
                    {/* Progress Bar */}
                    <div className="flex items-center justify-between mb-8 text-sm">
                        <div className={`flex flex-col items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${step >= 1 ? 'bg-blue-100 font-bold' : 'bg-gray-100'}`}>1</div>
                            <span>Connect</span>
                        </div>
                        <div className={`h-1 flex-1 mx-2 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
                        <div className={`flex flex-col items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${step >= 2 ? 'bg-blue-100 font-bold' : 'bg-gray-100'}`}>2</div>
                            <span>Verify</span>
                        </div>
                        <div className={`h-1 flex-1 mx-2 ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'}`} />
                        <div className={`flex flex-col items-center ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${step >= 3 ? 'bg-blue-100 font-bold' : 'bg-gray-100'}`}>3</div>
                            <span>Pull</span>
                        </div>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center gap-2 text-sm">
                            <AlertCircle className="h-4 w-4" />
                            {error}
                        </div>
                    )}

                    {/* Step 1: Connect */}
                    {step === 1 && (
                        <form onSubmit={handleConnect} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Select Provider</label>
                                <div className="grid grid-cols-2 gap-4">
                                    <button
                                        type="button"
                                        onClick={() => setProvider('MTN')}
                                        className={`p-3 border rounded-lg flex items-center justify-center gap-2 ${provider === 'MTN' ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:bg-gray-50'}`}
                                    >
                                        <span className="font-bold">MTN</span> Mobile Money
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setProvider('Airtel')}
                                        className={`p-3 border rounded-lg flex items-center justify-center gap-2 ${provider === 'Airtel' ? 'border-red-500 bg-red-50 text-red-700' : 'border-gray-200 hover:bg-gray-50'}`}
                                    >
                                        <span className="font-bold">Airtel</span> Money
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Wallet Number</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="e.g., 0961234567"
                                    value={walletNumber}
                                    onChange={(e) => setWalletNumber(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader className="h-4 w-4 animate-spin" /> : 'Request OTP'}
                            </button>
                        </form>
                    )}

                    {/* Step 2: Verify */}
                    {step === 2 && (
                        <form onSubmit={handleVerify} className="space-y-4">
                            <div className="text-center mb-4">
                                <p className="text-sm text-gray-600">Enter the OTP sent to</p>
                                <p className="font-medium text-gray-900">{walletNumber}</p>
                                <p className="text-xs text-gray-500 mt-1">(Mock: Use 123456 for MTN, 654321 for Airtel)</p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">OTP Code</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="Enter 6-digit code"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-center tracking-widest text-lg"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader className="h-4 w-4 animate-spin" /> : 'Verify Connection'}
                            </button>
                            <button
                                type="button"
                                onClick={() => setStep(1)}
                                className="w-full py-2 text-gray-600 hover:text-gray-800 text-sm"
                            >
                                Back to Connect
                            </button>
                        </form>
                    )}

                    {/* Step 3: Pull Data */}
                    {step === 3 && (
                        <form onSubmit={handlePull} className="space-y-4">
                            <div className="bg-green-50 p-4 rounded-lg flex items-center gap-3 mb-4">
                                <ShieldCheck className="h-6 w-6 text-green-600" />
                                <div>
                                    <p className="font-medium text-green-800">Connection Verified</p>
                                    <p className="text-xs text-green-600">Secure access established</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
                                    <input
                                        type="date"
                                        required
                                        value={dateRange.from}
                                        onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
                                    <input
                                        type="date"
                                        required
                                        value={dateRange.to}
                                        onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                    />
                                </div>
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader className="h-4 w-4 animate-spin" /> : <><Download className="h-4 w-4" /> Pull Statement</>}
                            </button>
                        </form>
                    )}

                    {/* Step 4: Success */}
                    {step === 4 && results && (
                        <div className="text-center space-y-4">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                                <CheckCircle className="h-8 w-8 text-green-600" />
                            </div>
                            <div>
                                <h4 className="text-xl font-bold text-gray-900">Import Successful!</h4>
                                <p className="text-gray-600 mt-1">
                                    Successfully pulled <span className="font-bold text-gray-900">{results.records_fetched}</span> transactions.
                                </p>
                            </div>
                            <div className="pt-4">
                                <button
                                    onClick={() => {
                                        reset();
                                        onClose();
                                    }}
                                    className="w-full py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
                                >
                                    Done
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TelcoConnect;
