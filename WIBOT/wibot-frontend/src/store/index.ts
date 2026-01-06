import { create } from 'zustand';
import type { User, Conversation, Message, ChatMode } from '../types';
import { getUser, getToken } from '../services/auth';

// ============================================
// AUTH STORE
// ============================================

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  setAuth: (user, token) => {
    set({
      user,
      token,
      isAuthenticated: true,
    });
  },

  clearAuth: () => {
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },
}));

// ============================================
// CONVERSATIONS STORE
// ============================================

interface ConversationsState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (conversationId: string, updates: Partial<Conversation>) => void;
  removeConversation: (conversationId: string) => void;
}

export const useConversationsStore = create<ConversationsState>((set) => ({
  conversations: [],
  currentConversation: null,

  setConversations: (conversations) => set({ conversations }),

  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),

  addConversation: (conversation) => set((state) => ({
    conversations: [conversation, ...state.conversations],
  })),

  updateConversation: (conversationId, updates) => set((state) => ({
    conversations: state.conversations.map((conv) =>
      conv.conversation_id === conversationId
        ? { ...conv, ...updates }
        : conv
    ),
    currentConversation: state.currentConversation?.conversation_id === conversationId
      ? { ...state.currentConversation, ...updates }
      : state.currentConversation,
  })),

  removeConversation: (conversationId) => set((state) => ({
    conversations: state.conversations.filter((conv) => conv.conversation_id !== conversationId),
    currentConversation: state.currentConversation?.conversation_id === conversationId
      ? null
      : state.currentConversation,
  })),
}));

// ============================================
// CHAT STORE
// ============================================

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  tokensRemaining: number;
  chatMode: ChatMode;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  setTokensRemaining: (tokens: number) => void;
  setChatMode: (mode: ChatMode) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  tokensRemaining: 50000, // Valeur par défaut
  chatMode: 'flash', // Mode par défaut: rapide et économique

  setMessages: (messages) => set({ messages }),

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),

  setLoading: (loading) => set({ isLoading: loading }),

  setTokensRemaining: (tokens) => set({ tokensRemaining: tokens }),

  setChatMode: (mode) => set({ chatMode: mode }),

  clearMessages: () => set({ messages: [] }),
}));
