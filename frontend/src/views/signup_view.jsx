import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Navigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, User, Briefcase, AlertCircle, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

import { registerUser, clearError, selectIsAuthenticated, selectIsLoading } from '../redux/slices/user_slice';
import LoadingSpinner from '../components/common/LoadingSpinner';

/**
 * Signup View Component
 * Handles user registration
 */
const Signup = () => {
    const dispatch = useDispatch();
    const isAuthenticated = useSelector(selectIsAuthenticated);
    const isLoading = useSelector(selectIsLoading);
    const error = useSelector(state => state.user.error);

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        first_name: '',
        last_name: '',
        business_name: '',
        terms_accepted: false,
        privacy_accepted: false,
    });

    const [showPassword, setShowPassword] = useState(false);

    // Clear any existing errors when component mounts
    useEffect(() => {
        dispatch(clearError());
    }, [dispatch]);

    // Redirect if already authenticated
    if (isAuthenticated) {
        return <Navigate to="/dashboard" replace />;
    }

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));

        // Clear error when user starts typing
        if (error) {
            dispatch(clearError());
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Basic Validation
        if (!formData.email || !formData.password || !formData.first_name || !formData.last_name || !formData.business_name) {
            toast.error('Please fill in all required fields');
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }

        if (!formData.terms_accepted || !formData.privacy_accepted) {
            toast.error('You must accept the Terms and Privacy Policy');
            return;
        }

        try {
            // Prepare data for API (exclude confirmPassword)
            const registrationData = {
                email: formData.email,
                password: formData.password,
                first_name: formData.first_name,
                last_name: formData.last_name,
                business_name: formData.business_name,
                terms_accepted: formData.terms_accepted,
                privacy_accepted: formData.privacy_accepted,
                gdpr_consent: true, // Assuming consent if they sign up
            };

            await dispatch(registerUser(registrationData)).unwrap();

            toast.success('Account created successfully!');
        } catch (error) {
            toast.error(error.message || 'Registration failed');
        }
    };

    return (
        <div className="login-page">
            <div className="auth-container" style={{ maxWidth: '500px' }}>
                {/* Header */}
                <div className="brand">
                    <div className="logo">Easy</div>
                    <p>Create your EasyFlow account</p>
                </div>

                {/* Signup Form */}
                <div className="card">
                    <form className="form" onSubmit={handleSubmit}>

                        {/* Name Fields */}
                        <div className="row between" style={{ gap: '1rem', alignItems: 'flex-start' }}>
                            <div className="field" style={{ flex: 1 }}>
                                <label htmlFor="first_name">First Name</label>
                                <div className="input-group">
                                    <span className="icon left"><User size={18} /></span>
                                    <input
                                        id="first_name"
                                        name="first_name"
                                        type="text"
                                        required
                                        value={formData.first_name}
                                        onChange={handleInputChange}
                                        className="input"
                                        placeholder="John"
                                    />
                                </div>
                            </div>
                            <div className="field" style={{ flex: 1 }}>
                                <label htmlFor="last_name">Last Name</label>
                                <div className="input-group">
                                    <span className="icon left"><User size={18} /></span>
                                    <input
                                        id="last_name"
                                        name="last_name"
                                        type="text"
                                        required
                                        value={formData.last_name}
                                        onChange={handleInputChange}
                                        className="input"
                                        placeholder="Doe"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Business Name */}
                        <div className="field">
                            <label htmlFor="business_name">Business Name</label>
                            <div className="input-group">
                                <span className="icon left"><Briefcase size={18} /></span>
                                <input
                                    id="business_name"
                                    name="business_name"
                                    type="text"
                                    required
                                    value={formData.business_name}
                                    onChange={handleInputChange}
                                    className="input"
                                    placeholder="Your Company Ltd."
                                />
                            </div>
                        </div>

                        {/* Email Field */}
                        <div className="field">
                            <label htmlFor="email">Email address</label>
                            <div className="input-group">
                                <span className="icon left"><Mail size={18} /></span>
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    autoComplete="email"
                                    required
                                    value={formData.email}
                                    onChange={handleInputChange}
                                    className="input"
                                    placeholder="name@company.com"
                                />
                            </div>
                        </div>

                        {/* Password Field */}
                        <div className="field">
                            <label htmlFor="password">Password</label>
                            <div className="input-group">
                                <span className="icon left"><Lock size={18} /></span>
                                <input
                                    id="password"
                                    name="password"
                                    type={showPassword ? 'text' : 'password'}
                                    autoComplete="new-password"
                                    required
                                    value={formData.password}
                                    onChange={handleInputChange}
                                    className="input with-right-icon"
                                    placeholder="Create a password"
                                />
                                <button
                                    type="button"
                                    className="icon-btn right"
                                    onClick={() => setShowPassword(!showPassword)}
                                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                        </div>

                        {/* Confirm Password Field */}
                        <div className="field">
                            <label htmlFor="confirmPassword">Confirm Password</label>
                            <div className="input-group">
                                <span className="icon left"><Lock size={18} /></span>
                                <input
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    type={showPassword ? 'text' : 'password'}
                                    autoComplete="new-password"
                                    required
                                    value={formData.confirmPassword}
                                    onChange={handleInputChange}
                                    className="input"
                                    placeholder="Confirm your password"
                                />
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="alert error">
                                <AlertCircle size={18} />
                                <span>{error}</span>
                            </div>
                        )}

                        {/* Terms & Privacy */}
                        <div className="field">
                            <label className="checkbox" style={{ alignItems: 'flex-start' }}>
                                <input
                                    id="terms_accepted"
                                    name="terms_accepted"
                                    type="checkbox"
                                    checked={formData.terms_accepted}
                                    onChange={handleInputChange}
                                    style={{ marginTop: '4px' }}
                                />
                                <span style={{ fontSize: '0.875rem' }}>
                                    I agree to the <Link to="/terms">Terms of Service</Link>
                                </span>
                            </label>
                            <label className="checkbox" style={{ alignItems: 'flex-start', marginTop: '0.5rem' }}>
                                <input
                                    id="privacy_accepted"
                                    name="privacy_accepted"
                                    type="checkbox"
                                    checked={formData.privacy_accepted}
                                    onChange={handleInputChange}
                                    style={{ marginTop: '4px' }}
                                />
                                <span style={{ fontSize: '0.875rem' }}>
                                    I agree to the <Link to="/privacy">Privacy Policy</Link>
                                </span>
                            </label>
                        </div>

                        {/* Submit Button */}
                        <div>
                            <button type="submit" disabled={isLoading} className="btn primary w-full">
                                {isLoading ? (
                                    <>
                                        <LoadingSpinner size="sm" />
                                        <span className="ml-8">Creating account...</span>
                                    </>
                                ) : (
                                    'Create Account'
                                )}
                            </button>
                        </div>

                    </form>
                </div>

                {/* Login Link */}
                <div className="footer-text">
                    <p>
                        Already have an account? <Link to="/login">Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Signup;
