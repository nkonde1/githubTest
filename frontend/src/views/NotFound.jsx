import React from 'react';
import { Link } from 'react-router-dom';

/**
 * @fileoverview NotFound View Component.
 *
 * This component displays a 404 "Page Not Found" message to the user
 * when they navigate to a non-existent URL. It provides a clear
 * indication of the error and offers a link back to the dashboard or home page
 * to improve user experience.
 */
const NotFound = () => {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 text-gray-800 p-4">
            <h1 className="text-9xl font-extrabold text-blue-600">404</h1>
            <p className="text-3xl font-semibold mb-4">Page Not Found</p>
            <p className="text-lg text-center mb-8 max-w-md">
                Oops! The page you're looking for doesn't exist or has been moved.
            </p>
            <Link
                to="/dashboard"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700 transition duration-300 ease-in-out font-medium"
            >
                Go to Dashboard
            </Link>
        </div>
    );
};

export default NotFound;