import type { User } from '../types';

const TOKEN_KEY = 'wibot_token';
const USER_KEY = 'wibot_user';

// ============================================
// TOKEN MANAGEMENT
// ============================================

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ============================================
// USER MANAGEMENT
// ============================================

export function saveUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getUser(): User | null {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;

  try {
    return JSON.parse(userStr) as User;
  } catch {
    return null;
  }
}

export function removeUser(): void {
  localStorage.removeItem(USER_KEY);
}

// ============================================
// AUTH STATUS
// ============================================

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function clearAuth(): void {
  removeToken();
  removeUser();
}
