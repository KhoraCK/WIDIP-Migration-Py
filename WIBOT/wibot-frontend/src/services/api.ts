import axios from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  ChatRequest,
  ChatResponse,
  Conversation,
  Message,
  AnalyticsResponse,
  AnalyticsPeriod,
  AdminUsersResponse,
  CreateUserRequest,
  UpdateUserRequest,
  AdminUserResponse,
  DeleteUserResponse
} from '../types';
import { getToken, removeToken } from './auth';

// Axios instance avec configuration de base
// En dev, le proxy Vite redirige /webhook vers localhost:8080
// En prod, VITE_API_URL pointe vers le serveur de production
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000, // 90 secondes pour les modeles lents (Mistral Large)
});

// Interceptor request : ajouter JWT si présent
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor response : gérer 401 (logout auto)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeToken();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// AUTH API
// ============================================

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/webhook/auth/login', credentials);
  return response.data;
}

// ============================================
// CONVERSATIONS API
// ============================================

export async function getConversations(): Promise<Conversation[]> {
  const response = await api.get<{ conversations: Conversation[] }>('/webhook/wibot/conversations');
  return response.data.conversations;
}

export async function createConversation(title?: string): Promise<Conversation> {
  const response = await api.post<{ conversation: Conversation }>('/webhook/wibot/conversations', { title });
  return response.data.conversation;
}

export async function getConversationMessages(conversationId: string): Promise<Message[]> {
  const response = await api.get<{ messages: Message[] }>(
    `/webhook/wibot/messages`,
    { params: { conversationId } }
  );
  return response.data.messages;
}

export async function renameConversation(conversationId: string, title: string): Promise<Conversation> {
  const response = await api.patch<{ success: boolean; conversation: Conversation }>(
    '/webhook/wibot/conversation/rename',
    { conversationId, title }
  );
  return response.data.conversation;
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await api.delete('/webhook/wibot/conversation/delete', {
    data: { conversationId }
  });
}

// ============================================
// CHAT API
// ============================================

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/webhook/wibot/chat', request);
  return response.data;
}

// ============================================
// TOKENS API
// ============================================

export interface TokensResponse {
  success: boolean;
  used_tokens: number;
  quota_tokens: number;
  tokens_remaining: number;
}

export async function getUserTokens(): Promise<TokensResponse> {
  const response = await api.get<TokensResponse>('/webhook/wibot/user/tokens');
  return response.data;
}

// ============================================
// ANALYTICS API (Admin only)
// ============================================

export async function getAnalytics(period: AnalyticsPeriod = '7d'): Promise<AnalyticsResponse> {
  const response = await api.get<AnalyticsResponse>('/webhook/wibot/analytics', {
    params: { period }
  });
  return response.data;
}

// ============================================
// ADMIN USERS API (Admin only)
// ============================================

export async function getAdminUsers(): Promise<AdminUsersResponse> {
  const response = await api.get<AdminUsersResponse>('/webhook/wibot/admin/users');
  return response.data;
}

export async function createUser(data: CreateUserRequest): Promise<AdminUserResponse> {
  const response = await api.post<AdminUserResponse>('/webhook/wibot/admin/users', data);
  return response.data;
}

export async function updateUser(data: UpdateUserRequest): Promise<AdminUserResponse> {
  const response = await api.put<AdminUserResponse>('/webhook/wibot/admin/users', data);
  return response.data;
}

export async function deleteUser(userId: number): Promise<DeleteUserResponse> {
  const response = await api.delete<DeleteUserResponse>('/webhook/wibot/admin/users', {
    data: { user_id: userId }
  });
  return response.data;
}

export default api;
