// frontend/src/redux/slices/aiChatSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api as http } from '../../services/api';
import { logoutUser } from './user_slice';

/**
 * Fetch conversation history from the backend
 */
export const fetchConversationHistory = createAsyncThunk(
  'aiChat/fetchConversationHistory',
  async (conversationId, { rejectWithValue }) => {
    try {
      const response = await http.get(`/api/v1/insights/chat/history/${conversationId}`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch conversation history');
    }
  }
);

/**
 * Send a message to the AI chat
 */
export const sendChatMessage = createAsyncThunk(
  'aiChat/sendMessage',
  async ({ conversationId, message }, { rejectWithValue }) => {
    try {
      const response = await http.post('/api/v1/insights/chat', {
        conversation_id: conversationId,
        content: message,
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to send message');
    }
  }
);

const initialState = {
  messages: [],
  conversationId: null,
  isLoading: false,
  isSending: false,
  error: null,
  lastUpdated: null,
};

const aiChatSlice = createSlice({
  name: 'aiChat',
  initialState,
  reducers: {
    // Set conversation ID
    setConversationId: (state, action) => {
      state.conversationId = action.payload;
      // Save to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('ai_chat_conversation_id', action.payload);
      }
    },

    // Add a message to the chat
    addMessage: (state, action) => {
      state.messages.push({
        ...action.payload,
        timestamp: action.payload.timestamp || new Date().toISOString(),
      });
      state.lastUpdated = new Date().toISOString();
    },

    // Clear all messages
    clearMessages: (state) => {
      state.messages = [];
      state.error = null;
    },

    // Load messages from stored state
    loadMessages: (state, action) => {
      state.messages = action.payload || [];
      state.lastUpdated = new Date().toISOString();
    },

    // Clear error
    clearError: (state) => {
      state.error = null;
    },

    // Initialize conversation ID from localStorage
    initializeConversationId: (state) => {
      if (typeof window !== 'undefined') {
        const storedId = localStorage.getItem('ai_chat_conversation_id');
        if (storedId) {
          state.conversationId = storedId;
        } else {
          // Generate new conversation ID
          const newId = Math.random().toString(36).slice(2);
          state.conversationId = newId;
          localStorage.setItem('ai_chat_conversation_id', newId);
        }
      } else {
        // Generate new conversation ID if no localStorage
        state.conversationId = Math.random().toString(36).slice(2);
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch conversation history
      .addCase(fetchConversationHistory.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchConversationHistory.fulfilled, (state, action) => {
        state.isLoading = false;
        // Convert backend conversation format to frontend message format
        if (action.payload && action.payload.messages) {
          state.messages = action.payload.messages.map((msg) => ({
            sender: msg.role === 'user' ? 'user' : 'ai',
            text: msg.content || msg.text,
            timestamp: msg.timestamp || msg.ts || new Date().toISOString(),
          }));
        }
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchConversationHistory.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload || 'Failed to load conversation history';
      })

      // Send message
      .addCase(sendChatMessage.pending, (state) => {
        state.isSending = true;
        state.error = null;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.isSending = false;
        // Add AI response to messages
        if (action.payload.response) {
          state.messages.push({
            sender: 'ai',
            text: action.payload.response,
            timestamp: action.payload.timestamp || new Date().toISOString(),
          });
        }
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.isSending = false;
        state.error = action.payload || 'Failed to send message';
        // Add error message to chat
        state.messages.push({
          sender: 'ai',
          text: 'Oops! Something went wrong. Please try again.',
          timestamp: new Date().toISOString(),
        });
      })

      // Handle logout - clear chat state
      .addCase(logoutUser.fulfilled, (state) => {
        state.messages = [];
        state.conversationId = null;
        state.error = null;
        state.isLoading = false;
        // Clear from localStorage
        if (typeof window !== 'undefined') {
          localStorage.removeItem('ai_chat_conversation_id');
        }
      });
  },
});

export const {
  setConversationId,
  addMessage,
  clearMessages,
  loadMessages,
  clearError,
  initializeConversationId,
} = aiChatSlice.actions;

export default aiChatSlice.reducer;

