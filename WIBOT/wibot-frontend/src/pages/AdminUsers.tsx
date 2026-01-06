import { useState, useEffect, useCallback } from 'react';
import { Navigate } from 'react-router-dom';
import { Users, Plus, Trash2, Coins, UserCog, RefreshCw, Shield } from 'lucide-react';
import { useAuthStore } from '../store';
import { getAdminUsers, createUser, updateUser, deleteUser } from '../services/api';
import type { AdminUser, CreateUserRequest, AccreditationLevel } from '../types';
import { Spinner, LevelSelector, LevelBadge } from '../components/ui';
import { Header } from '../components/layout/Header';

export function AdminUsers() {
  const { user } = useAuthStore();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTokensModal, setShowTokensModal] = useState(false);
  const [showLevelModal, setShowLevelModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);

  // Form states
  const [newUser, setNewUser] = useState<CreateUserRequest>({
    username: '',
    password: '',
    email: '',
    role: 'user',
    quota_tokens: 50000,
    accreditation_level: 'N1'
  });
  const [addTokens, setAddTokens] = useState(10000);
  const [newLevel, setNewLevel] = useState<AccreditationLevel>('N1');

  // Redirect non-admin users
  if (user?.role !== 'admin') {
    return <Navigate to="/chat" replace />;
  }

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getAdminUsers();
      setUsers(response.users);
    } catch (err) {
      setError('Erreur lors du chargement des utilisateurs');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createUser(newUser);
      setShowCreateModal(false);
      setNewUser({ username: '', password: '', email: '', role: 'user', quota_tokens: 50000, accreditation_level: 'N1' });
      fetchUsers();
    } catch (err) {
      setError('Erreur lors de la création de l\'utilisateur');
      console.error(err);
    }
  };

  const handleUpdateLevel = async () => {
    if (!selectedUser) return;
    try {
      await updateUser({ user_id: selectedUser.user_id, accreditation_level: newLevel });
      setShowLevelModal(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (err) {
      setError('Erreur lors de la modification du niveau');
      console.error(err);
    }
  };

  const handleAddTokens = async () => {
    if (!selectedUser) return;
    try {
      await updateUser({ user_id: selectedUser.user_id, add_tokens: addTokens });
      setShowTokensModal(false);
      setSelectedUser(null);
      setAddTokens(10000);
      fetchUsers();
    } catch (err) {
      setError('Erreur lors de l\'ajout de tokens');
      console.error(err);
    }
  };

  const handleToggleActive = async (u: AdminUser) => {
    try {
      await updateUser({ user_id: u.user_id, is_active: !u.is_active });
      fetchUsers();
    } catch (err) {
      setError('Erreur lors de la modification');
      console.error(err);
    }
  };

  const handleDeleteUser = async (u: AdminUser) => {
    if (!confirm(`Supprimer l'utilisateur "${u.username}" ?`)) return;
    try {
      await deleteUser(u.user_id);
      fetchUsers();
    } catch (err) {
      setError('Erreur lors de la suppression');
      console.error(err);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Header principal */}
      <Header />

      {/* Sous-header Utilisateurs */}
      <div className="bg-bg-secondary border-b border-border px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Users className="w-5 h-5 text-accent" />
            Gestion des utilisateurs
          </h1>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchUsers}
              className="p-2 text-text-secondary hover:text-text-primary hover:bg-bg-primary rounded-lg transition-colors"
              title="Rafraichir"
            >
              <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              Nouvel utilisateur
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="bg-bg-secondary border border-border rounded-xl overflow-hidden">
            <table className="w-full">
              <thead className="bg-bg-primary">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-medium text-text-secondary">Utilisateur</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-text-secondary">Email</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-text-secondary">Role</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-text-secondary">Niveau</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-text-secondary">Tokens</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-text-secondary">Statut</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-text-secondary">Cree le</th>
                  <th className="px-6 py-4 text-right text-sm font-medium text-text-secondary">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map((u) => (
                  <tr key={u.user_id} className="hover:bg-bg-primary/50 transition-colors">
                    <td className="px-6 py-4">
                      <span className="font-medium text-text-primary">{u.username}</span>
                    </td>
                    <td className="px-6 py-4 text-text-secondary">
                      {u.email || '-'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        u.role === 'admin'
                          ? 'bg-purple-500/20 text-purple-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <LevelBadge level={u.accreditation_level || 'N1'} />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <span className="text-text-primary">
                          {u.used_tokens.toLocaleString('fr-FR')} / {u.quota_tokens.toLocaleString('fr-FR')}
                        </span>
                        <div className="w-24 h-1.5 bg-bg-primary rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              (u.used_tokens / u.quota_tokens) > 0.9 ? 'bg-red-500' :
                              (u.used_tokens / u.quota_tokens) > 0.7 ? 'bg-orange-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${Math.min(100, (u.used_tokens / u.quota_tokens) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleToggleActive(u)}
                        className={`px-2 py-1 rounded-full text-xs font-medium transition-colors ${
                          u.is_active
                            ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                            : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                        }`}
                      >
                        {u.is_active ? 'Actif' : 'Inactif'}
                      </button>
                    </td>
                    <td className="px-6 py-4 text-text-secondary text-sm">
                      {formatDate(u.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => { setSelectedUser(u); setNewLevel(u.accreditation_level || 'N1'); setShowLevelModal(true); }}
                          className="p-2 text-text-secondary hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                          title="Modifier le niveau"
                        >
                          <Shield className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => { setSelectedUser(u); setShowTokensModal(true); }}
                          className="p-2 text-text-secondary hover:text-orange-400 hover:bg-orange-500/10 rounded-lg transition-colors"
                          title="Ajouter des tokens"
                        >
                          <Coins className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteUser(u)}
                          className="p-2 text-text-secondary hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                          title="Supprimer"
                          disabled={u.user_id === user?.id}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* Modal: Create User */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-bg-secondary border border-border rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-accent/10 rounded-lg">
                <UserCog className="w-5 h-5 text-accent" />
              </div>
              <h2 className="text-lg font-semibold text-text-primary">Nouvel utilisateur</h2>
            </div>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Nom d'utilisateur *
                </label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="w-full px-4 py-2 bg-bg-primary border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Mot de passe *
                </label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full px-4 py-2 bg-bg-primary border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="w-full px-4 py-2 bg-bg-primary border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Role
                </label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="w-full px-4 py-2 bg-bg-primary border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="user">Utilisateur</option>
                  <option value="admin">Administrateur</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Niveau d'accreditation Safeguard
                </label>
                <LevelSelector
                  value={newUser.accreditation_level || 'N1'}
                  onChange={(level) => setNewUser({ ...newUser, accreditation_level: level })}
                  size="sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Quota tokens mensuel
                </label>
                <input
                  type="number"
                  value={newUser.quota_tokens}
                  onChange={(e) => setNewUser({ ...newUser, quota_tokens: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-bg-primary border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                  min={0}
                  step={1000}
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-text-secondary hover:text-text-primary transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg transition-colors"
                >
                  Creer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Tokens */}
      {showTokensModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-bg-secondary border border-border rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-orange-500/10 rounded-lg">
                <Coins className="w-5 h-5 text-orange-400" />
              </div>
              <h2 className="text-lg font-semibold text-text-primary">
                Ajouter des tokens a {selectedUser.username}
              </h2>
            </div>
            <div className="space-y-4">
              <div className="p-4 bg-bg-primary rounded-lg">
                <p className="text-sm text-text-secondary">Tokens actuels</p>
                <p className="text-xl font-bold text-text-primary">
                  {selectedUser.used_tokens.toLocaleString('fr-FR')} / {selectedUser.quota_tokens.toLocaleString('fr-FR')}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Tokens a ajouter
                </label>
                <input
                  type="number"
                  value={addTokens}
                  onChange={(e) => setAddTokens(parseInt(e.target.value))}
                  className="w-full px-4 py-2 bg-bg-primary border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                  min={0}
                  step={1000}
                />
              </div>
              <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                <p className="text-sm text-green-400">
                  Nouveau quota: {(selectedUser.quota_tokens + addTokens).toLocaleString('fr-FR')} tokens
                </p>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowTokensModal(false); setSelectedUser(null); }}
                  className="px-4 py-2 text-text-secondary hover:text-text-primary transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={handleAddTokens}
                  className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition-colors"
                >
                  Ajouter
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Change Level */}
      {showLevelModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-bg-secondary border border-border rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Shield className="w-5 h-5 text-blue-400" />
              </div>
              <h2 className="text-lg font-semibold text-text-primary">
                Niveau de {selectedUser.username}
              </h2>
            </div>
            <div className="space-y-4">
              <div className="p-4 bg-bg-primary rounded-lg">
                <p className="text-sm text-text-secondary mb-2">Niveau actuel</p>
                <LevelBadge level={selectedUser.accreditation_level || 'N1'} />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Nouveau niveau
                </label>
                <LevelSelector
                  value={newLevel}
                  onChange={setNewLevel}
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowLevelModal(false); setSelectedUser(null); }}
                  className="px-4 py-2 text-text-secondary hover:text-text-primary transition-colors"
                >
                  Annuler
                </button>
                <button
                  onClick={handleUpdateLevel}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
