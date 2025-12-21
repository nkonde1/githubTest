import React, { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { marked } from 'marked'; // For rendering markdown in AI responses
import DOMPurify from 'dompurify'; // For sanitizing HTML from markdown output
import {
    initializeConversationId,
    fetchConversationHistory,
    sendChatMessage,
    addMessage,
} from '../../redux/slices/aiChatSlice';

/**
 * @typedef {Object} Message
 * @property {'user' | 'ai'} sender - The sender of the message.
 * @property {string} text - The content of the message.
 * @property {string} timestamp - The timestamp when the message was sent/received.
 */

/**
 * AIChat Component
 *
 * This component provides a conversational interface for users to interact with
 * the AI agent. It allows users to send messages and displays AI responses,
 * including dynamic insights and recommendations.
 *
 * Features:
 * - Real-time chat interface.
 * - Displays user and AI messages.
 * - Handles sending messages to the backend AI endpoint.
 * - Renders AI responses, potentially including markdown.
 * - Loading indicator for AI responses.
 * - Automatic scrolling to the latest message.
 * - Basic error handling for API calls.
 * - Persistent conversation history across page navigation.
 */
const AIChat = () => {
    const dispatch = useDispatch();
    
    // Get chat state from Redux
    const { messages, conversationId, isLoading, isSending, error } = useSelector(
        (state) => state.aiChat || {
            messages: [],
            conversationId: null,
            isLoading: false,
            isSending: false,
            error: null,
        }
    );
    
    /** @type {[string, React.Dispatch<React.SetStateAction<string>>]} */
    const [inputValue, setInputValue] = useState('');
    /** @type {React.RefObject<HTMLDivElement>} */
    const messagesEndRef = useRef(null);

    // Initialize conversation ID on mount
    useEffect(() => {
        dispatch(initializeConversationId());
    }, [dispatch]);

    // Load conversation history when conversation ID is available
    useEffect(() => {
        if (conversationId && messages.length === 0 && !isLoading) {
            dispatch(fetchConversationHistory(conversationId));
        }
    }, [conversationId, dispatch]); // Only run when conversationId changes

    /**
     * Scrolls to the bottom of the chat messages container.
     */
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // Effect to scroll to bottom whenever messages update
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    /**
     * Handles sending a message to the AI agent.
     *
     * @param {React.FormEvent<HTMLFormElement>} e - The form submission event.
     */
    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (inputValue.trim() === '' || !conversationId) return;

        // Add user message immediately to Redux
        dispatch(addMessage({
            sender: 'user',
            text: inputValue,
            timestamp: new Date().toISOString(),
        }));

        const messageText = inputValue;
        setInputValue('');

        // Send message to backend
        try {
            await dispatch(sendChatMessage({
                conversationId,
                message: messageText,
            })).unwrap();
        } catch (error) {
            console.error('Error sending message to AI:', error);
            // Error message is already added by the rejected action
        }
    };

    /**
     * Renders a message bubble.
     *
     * @param {Message} message - The message object to render.
     * @returns {JSX.Element} The message bubble JSX.
     */
    const renderMessage = (message) => {
        const isUser = message.sender === 'user';
        const bubbleClasses = isUser
            ? 'bg-blue-500 text-white self-end rounded-br-none'
            : 'bg-gray-200 text-gray-800 self-start rounded-bl-none';
        const alignmentClasses = isUser ? 'items-end' : 'items-start';

        // Sanitize and dangerously set inner HTML for AI markdown responses
        const createMarkup = () => {
            const cleanHtml = DOMPurify.sanitize(marked.parse(message.text));
            return { __html: cleanHtml };
        };

        return (
            <div className={`flex flex-col ${alignmentClasses} mb-4 max-w-[75%]`}>
                <div className={`p-3 rounded-lg shadow-md ${bubbleClasses}`}>
                    <div
                        className="prose prose-sm break-words" // Tailwind Typography for markdown styling
                        dangerouslySetInnerHTML={createMarkup()}
                    />
                </div>
                <span className="text-xs text-gray-500 mt-1">
                    {isUser ? 'You' : 'AI'} • {message.timestamp}
                </span>
            </div>
        );
    };

    return (
        <div className="flex flex-col h-full bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4 border-b pb-2">AI Assistant</h2>

            {/* Message Display Area */}
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                {messages.length === 0 && !isLoading && (
                    <div className="flex justify-center items-center h-full text-gray-500 text-lg">
                        <p>Ask me anything about your business!</p>
                    </div>
                )}
                {messages.map((msg, index) => (
                    <React.Fragment key={`${msg.timestamp}-${index}`}>
                        {renderMessage(msg)}
                    </React.Fragment>
                ))}
                {(isSending || isLoading) && (
                    <div className="flex self-start mb-4 max-w-[75%]">
                        <div className="bg-gray-200 text-gray-800 p-3 rounded-lg shadow-md rounded-bl-none">
                            <span className="animate-pulse">Thinking...</span>
                        </div>
                    </div>
                )}
                {error && (
                    <div className="flex self-start mb-4 max-w-[75%]">
                        <div className="bg-red-100 text-red-800 p-3 rounded-lg shadow-md rounded-bl-none">
                            <span>{error}</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} /> {/* For auto-scrolling */}
            </div>

            {/* Message Input Area */}
            <form onSubmit={handleSendMessage} className="mt-4 flex gap-2">
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Type your message here..."
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-200 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isSending || isLoading || !conversationId}
                >
                    {isSending ? 'Sending...' : 'Send'}
                </button>
            </form>
        </div>
    );
};

export default AIChat;