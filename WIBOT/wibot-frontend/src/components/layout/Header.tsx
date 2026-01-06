import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LogOut, User, ChevronDown, Coins, BarChart3, Users, Shield } from 'lucide-react';
import { useAuthStore, useChatStore } from '../../store';
import { useSafeguardStore } from '../../store/safeguardStore';
import { useAuth } from '../../hooks/useAuth';

export function Header() {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { user } = useAuthStore();
  const { tokensRemaining } = useChatStore();
  const { pendingCount } = useSafeguardStore();
  const { logout } = useAuth();

  // Fermer le dropdown quand on clique ailleurs
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Formater le nombre de tokens
  const formatTokens = (tokens: number): string => {
    return tokens.toLocaleString('fr-FR');
  };

  // Calculer le pourcentage de tokens restants
  const maxTokens = 50000;
  const tokenPercentage = (tokensRemaining / maxTokens) * 100;

  // Déterminer la couleur selon le niveau
  const getTokenColor = () => {
    if (tokensRemaining <= 0) return 'text-red-500';
    if (tokensRemaining < 5000) return 'text-orange-400';
    if (tokensRemaining < 15000) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getProgressColor = () => {
    if (tokensRemaining <= 0) return 'bg-red-500';
    if (tokensRemaining < 5000) return 'bg-orange-400';
    if (tokensRemaining < 15000) return 'bg-yellow-400';
    return 'bg-green-400';
  };

  return (
    <header className="h-header bg-bg-secondary border-b border-border flex items-center justify-between px-6">
      {/* Logo cliquable - retour au chat */}
      <Link
        to="/chat"
        className="flex items-center gap-3 hover:opacity-80 transition-opacity"
        title="Retour au chat"
      >
        <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">W</span>
        </div>
        <h1 className="text-xl font-bold text-text-primary">WIBOT</h1>
      </Link>

      {/* Droite : Tokens + User */}
      <div className="flex items-center gap-6">
        {/* Compteur tokens amélioré */}
        <div className="flex items-center gap-3">
          <Coins className={`w-5 h-5 ${getTokenColor()}`} />
          <div className="flex flex-col">
            <div className="flex items-baseline gap-1">
              <span className={`font-semibold ${getTokenColor()}`}>
                {formatTokens(tokensRemaining)}
              </span>
              <span className="text-xs text-text-secondary">/ {formatTokens(maxTokens)}</span>
            </div>
            {/* Barre de progression */}
            <div className="w-24 h-1.5 bg-bg-primary rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${getProgressColor()}`}
                style={{ width: `${Math.max(0, Math.min(100, tokenPercentage))}%` }}
              />
            </div>
          </div>
          {/* Warning si tokens bas */}
          {tokensRemaining <= 0 && (
            <span className="text-xs text-red-400 font-medium px-2 py-0.5 bg-red-500/10 rounded">
              Epuise
            </span>
          )}
          {tokensRemaining > 0 && tokensRemaining < 5000 && (
            <span className="text-xs text-orange-400 font-medium px-2 py-0.5 bg-orange-500/10 rounded">
              Bas
            </span>
          )}
        </div>

        {/* Séparateur */}
        <div className="h-8 w-px bg-border" />

        {/* User dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-bg-primary transition-colors"
          >
            <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <span className="text-text-primary font-medium hidden sm:block">
              {user?.username || 'Utilisateur'}
            </span>
            <ChevronDown
              className={`w-4 h-4 text-text-secondary transition-transform duration-200 ${
                isDropdownOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {/* Dropdown menu */}
          {isDropdownOpen && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-bg-secondary border border-border rounded-lg shadow-xl py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="px-4 py-2 border-b border-border">
                <p className="text-sm text-text-primary font-medium">{user?.username}</p>
                <p className="text-xs text-text-secondary capitalize">{user?.role}</p>
              </div>
              {/* Admin links */}
              {user?.role === 'admin' && (
                <>
                  <Link
                    to="/supervision"
                    onClick={() => setIsDropdownOpen(false)}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-bg-primary transition-colors"
                  >
                    <BarChart3 className="w-4 h-4" />
                    Supervision
                  </Link>
                  <Link
                    to="/admin/users"
                    onClick={() => setIsDropdownOpen(false)}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-bg-primary transition-colors"
                  >
                    <Users className="w-4 h-4" />
                    Utilisateurs
                  </Link>
                  <Link
                    to="/safeguard"
                    onClick={() => setIsDropdownOpen(false)}
                    className="w-full flex items-center justify-between px-4 py-2 text-sm text-text-primary hover:bg-bg-primary transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      Safeguard
                    </span>
                    {pendingCount > 0 && (
                      <span className="px-1.5 py-0.5 text-xs font-medium bg-red-500 text-white rounded-full min-w-[20px] text-center">
                        {pendingCount > 99 ? '99+' : pendingCount}
                      </span>
                    )}
                  </Link>
                </>
              )}
              <button
                onClick={() => {
                  setIsDropdownOpen(false);
                  logout();
                }}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-bg-primary transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Se deconnecter
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
