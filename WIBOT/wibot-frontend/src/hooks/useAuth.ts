import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store';
import { login as apiLogin } from '../services/api';
import { saveToken, saveUser, clearAuth as clearAuthStorage } from '../services/auth';

interface UseAuthReturn {
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
}

export function useAuth(): UseAuthReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const { setAuth, clearAuth } = useAuthStore();

  const login = async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiLogin({ username, password });

      if (response.success) {
        // Sauvegarder dans localStorage
        saveToken(response.token);
        saveUser(response.user);

        // Mettre à jour le store
        setAuth(response.user, response.token);

        // Rediriger vers /chat
        navigate('/chat');
        return true;
      } else {
        setError('Identifiants incorrects');
        return false;
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message || 'Erreur de connexion');
      } else {
        setError('Erreur de connexion au serveur');
      }
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    // Nettoyer le store en premier
    clearAuth();

    // Ensuite nettoyer localStorage
    clearAuthStorage();

    // Rediriger vers /login
    navigate('/login', { replace: true });
  };

  return {
    isLoading,
    error,
    login,
    logout,
  };
}
