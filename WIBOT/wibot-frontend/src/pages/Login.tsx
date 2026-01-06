import { useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { Button, Input } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { useAuthStore } from '../store';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const { login, isLoading, error } = useAuth();
  const { isAuthenticated } = useAuthStore();

  // Si déjà authentifié, rediriger vers /chat
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (username.trim() && password.trim()) {
      await login(username.trim(), password);
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center p-4">
      {/* Background gradient subtil */}
      <div className="absolute inset-0 bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary" />

      {/* Card de login */}
      <div className="relative w-full max-w-md">
        <div className="bg-bg-secondary border border-border rounded-2xl p-8 shadow-2xl">
          {/* Logo */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-text-primary mb-2">WIBOT</h1>
            <p className="text-text-secondary">Connectez-vous pour continuer</p>
          </div>

          {/* Formulaire */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-text-primary mb-2"
              >
                Nom d'utilisateur
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Entrez votre nom d'utilisateur"
                disabled={isLoading}
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-text-primary mb-2"
              >
                Mot de passe
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Entrez votre mot de passe"
                disabled={isLoading}
              />
            </div>

            {/* Message d'erreur */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3">
                <p className="text-red-400 text-sm text-center">{error}</p>
              </div>
            )}

            {/* Bouton submit */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={isLoading}
              disabled={!username.trim() || !password.trim()}
              className="w-full"
            >
              {isLoading ? 'Connexion...' : 'Se connecter'}
            </Button>
          </form>

          {/* Footer */}
          <p className="text-center text-text-secondary text-sm mt-8">
            Chatbot interne WIDIP
          </p>
        </div>
      </div>
    </div>
  );
}
