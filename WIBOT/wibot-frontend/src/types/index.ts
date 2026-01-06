// ============================================
// TYPES BACKEND (Référence API n8n)
// ============================================

// Auth
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  token: string;
  user: User;
}

export interface User {
  id: number;
  username: string;
  role: string;
}

// Chat Modes
export type ChatMode = 'code' | 'flash' | 'redaction';

export interface ChatModeConfig {
  id: ChatMode;
  label: string;
  description: string;
}

// Chat
export interface ChatRequest {
  conversation_id: string;
  message: string;
  mode: ChatMode;
  files?: FileAttachment[];
}

export interface FileAttachment {
  name: string;
  content: string;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  tokens_used: number;
  tokens_remaining: number;
  conversation_id: string;
}

// Conversations
export interface Conversation {
  conversation_id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

// Messages
export interface Message {
  message_id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

// ============================================
// TYPES UI
// ============================================

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  onClick?: () => void;
  children: React.ReactNode;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export interface InputProps {
  type?: 'text' | 'password' | 'email';
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
  name?: string;
}

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// ============================================
// ANALYTICS TYPES
// ============================================

export type AnalyticsPeriod = '24h' | '7d' | '30d';

export interface AnalyticsTokens {
  used: number;
  quota: number;
  percentage: number;
}

export interface AnalyticsMessagesByDay {
  date: string;
  count: number;
  tokens: number;
}

export interface AnalyticsModes {
  flash: number;
  code: number;
  redaction: number;
}

export interface AnalyticsConversations {
  total: number;
  active: number;
}

export interface AnalyticsUsers {
  total: number;
}

export interface AnalyticsFiles {
  total: number;
  messagesWithFiles: number;
}

export interface AnalyticsRag {
  queries: number;
}

export interface AnalyticsStats {
  tokens: AnalyticsTokens;
  messages: {
    total: number;
    today: number;
    byDay: AnalyticsMessagesByDay[];
  };
  modes: AnalyticsModes;
  conversations: AnalyticsConversations;
  users: AnalyticsUsers;
  files: AnalyticsFiles;
  rag: AnalyticsRag;
}

export interface AnalyticsResponse {
  success: boolean;
  period: AnalyticsPeriod;
  stats: AnalyticsStats;
}

// ============================================
// ACCREDITATION LEVELS (SAFEGUARD)
// ============================================

export type AccreditationLevel = 'N0' | 'N1' | 'N2' | 'N3' | 'N4';

export const ACCREDITATION_LABELS: Record<AccreditationLevel, string> = {
  N0: 'Lecture seule',
  N1: 'Technicien',
  N2: 'Technicien Senior',
  N3: 'Admin',
  N4: 'Super Admin',
};

export const ACCREDITATION_DESCRIPTIONS: Record<AccreditationLevel, string> = {
  N0: 'Peut voir les demandes uniquement',
  N1: 'Peut approuver les actions L1',
  N2: 'Peut approuver les actions L1 et L2',
  N3: 'Peut approuver les actions L1, L2 et L3',
  N4: 'Accès complet + gestion utilisateurs',
};

export const ACCREDITATION_COLORS: Record<AccreditationLevel, string> = {
  N0: 'text-gray-400 bg-gray-500/20',
  N1: 'text-blue-400 bg-blue-500/20',
  N2: 'text-green-400 bg-green-500/20',
  N3: 'text-orange-400 bg-orange-500/20',
  N4: 'text-red-400 bg-red-500/20',
};

// ============================================
// ADMIN USERS TYPES
// ============================================

export interface AdminUser {
  user_id: number;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  used_tokens: number;
  quota_tokens: number;
  accreditation_level: AccreditationLevel;
}

export interface AdminUsersResponse {
  success: boolean;
  users: AdminUser[];
}

export interface CreateUserRequest {
  username: string;
  password: string;
  email?: string;
  role?: string;
  quota_tokens?: number;
  accreditation_level?: AccreditationLevel;
}

export interface UpdateUserRequest {
  user_id: number;
  quota_tokens?: number;
  add_tokens?: number;
  role?: string;
  is_active?: boolean;
  accreditation_level?: AccreditationLevel;
}

export interface AdminUserResponse {
  success: boolean;
  user: AdminUser;
}

export interface DeleteUserResponse {
  success: boolean;
  deleted: { user_id: number; username: string };
}

// ============================================
// STORE TYPES
// ============================================

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User, token: string) => void;
  clearUser: () => void;
}

export interface ConversationsState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addConversation: (conversation: Conversation) => void;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  tokensRemaining: number;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  setTokensRemaining: (tokens: number) => void;
  clearMessages: () => void;
}
