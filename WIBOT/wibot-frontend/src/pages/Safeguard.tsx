import { useState, useEffect, useCallback, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { Header } from '../components/layout/Header';
import { useAuthStore } from '../store';
import { useSafeguardStore } from '../store/safeguardStore';
import { useToastStore } from '../store/toastStore';
import {
  RequestList,
  RequestDetail,
  RequestDetailEmpty,
} from '../components/safeguard';
import type { SafeguardRequest } from '../components/safeguard';
import { Spinner } from '../components/ui';

// Fonction pour générer des mock data avec des timestamps frais
function generateMockRequests(): SafeguardRequest[] {
  return [
    {
      approval_id: 'APR-2026-001',
      tool_name: 'ad_reset_password',
      arguments: { username: 'jdupont', domain: 'widip.local' },
      security_level: 'L3',
      status: 'pending',
      created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      expires_at: new Date(Date.now() + 45 * 60 * 1000).toISOString(),
      time_remaining_seconds: 45 * 60,
      context: {
        ticket_id: 1234,
        client_name: 'EHPAD Les Music Art',
        description: 'Reset mot de passe demandé par Mme Martin (secrétariat)',
      },
    },
    {
      approval_id: 'APR-2026-002',
      tool_name: 'glpi_close_ticket',
      arguments: { ticket_id: 5678 },
      security_level: 'L3',
      status: 'pending',
      created_at: new Date(Date.now() - 28 * 60 * 1000).toISOString(),
      expires_at: new Date(Date.now() + 32 * 60 * 1000).toISOString(),
      time_remaining_seconds: 32 * 60,
      context: {
        ticket_id: 5678,
        client_name: 'Clinique Saint Joseph',
        description: 'Fermeture ticket après résolution problème imprimante',
      },
    },
  ];
}

export function Safeguard() {
  const { user } = useAuthStore();
  const toast = useToastStore();
  const {
    requests,
    selectedRequest,
    isLoading,
    isActionLoading,
    error,
    pollingInterval,
    isPollingEnabled,
    setSelectedRequest,
    setRequests,
    setLoading,
    fetchRequests,
    approveRequest,
    rejectRequest,
  } = useSafeguardStore();

  const [comment, setComment] = useState('');
  const [useMockData, setUseMockData] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const pollingRef = useRef<number | null>(null);

  // Chargement initial - charger les données
  useEffect(() => {
    if (user?.role !== 'admin') return;
    if (initialized) return;

    // Marquer comme initialisé immédiatement pour éviter les doubles appels
    setInitialized(true);

    const loadData = async () => {
      try {
        // Tenter l'appel API
        await fetchRequests();
        console.log('Safeguard: Données chargées depuis l\'API');
      } catch (err) {
        // Si l'API échoue, utiliser les mock data
        console.warn('API Safeguard non disponible, utilisation des données de test', err);
        setUseMockData(true);
        setRequests(generateMockRequests());
        setLoading(false);
      }
    };

    loadData();
  }, [user?.role, initialized, fetchRequests, setRequests, setLoading]);

  // Polling automatique (désactivé pour l'instant car pas de backend)
  useEffect(() => {
    if (isPollingEnabled && pollingInterval > 0 && !useMockData && initialized) {
      pollingRef.current = window.setInterval(() => {
        fetchRequests(false).catch(() => {
          // Ignorer les erreurs de polling silencieusement
        });
      }, pollingInterval);
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [isPollingEnabled, pollingInterval, useMockData, initialized, fetchRequests]);

  // Mise à jour countdown pour mock data
  useEffect(() => {
    if (!useMockData) return;

    const interval = setInterval(() => {
      setRequests(
        requests.map(req => ({
          ...req,
          time_remaining_seconds: Math.max(0, req.time_remaining_seconds - 30),
        }))
      );
    }, 30000);

    return () => clearInterval(interval);
  }, [useMockData, requests, setRequests]);

  // Sélectionner la première demande par défaut
  useEffect(() => {
    if (requests.length > 0 && !selectedRequest) {
      const pending = requests.filter(r => r.status === 'pending');
      if (pending.length > 0) {
        setSelectedRequest(pending[0]);
      }
    }
  }, [requests, selectedRequest, setSelectedRequest]);

  // Handlers
  const handleApprove = useCallback(async () => {
    if (!selectedRequest) return;

    if (useMockData) {
      // Mock: simuler l'approbation
      setRequests(requests.filter(r => r.approval_id !== selectedRequest.approval_id));
      setSelectedRequest(null);
      setComment('');
      toast.success('Demande approuvée avec succès');
      return;
    }

    const success = await approveRequest(selectedRequest.approval_id, comment);
    if (success) {
      setComment('');
      toast.success('Demande approuvée avec succès');
    } else {
      toast.error(error || 'Erreur lors de l\'approbation');
    }
  }, [selectedRequest, useMockData, requests, comment, approveRequest, error, toast, setRequests, setSelectedRequest]);

  const handleReject = useCallback(async () => {
    if (!selectedRequest) return;

    if (useMockData) {
      // Mock: simuler le refus
      setRequests(requests.filter(r => r.approval_id !== selectedRequest.approval_id));
      setSelectedRequest(null);
      setComment('');
      toast.warning('Demande refusée');
      return;
    }

    const success = await rejectRequest(selectedRequest.approval_id, comment);
    if (success) {
      setComment('');
      toast.warning('Demande refusée');
    } else {
      toast.error(error || 'Erreur lors du refus');
    }
  }, [selectedRequest, useMockData, requests, comment, rejectRequest, error, toast, setRequests, setSelectedRequest]);

  const handleRefresh = useCallback(() => {
    if (useMockData) {
      setRequests(generateMockRequests());
      toast.success('Données actualisées');
      return;
    }
    fetchRequests().catch(() => {
      // En cas d'erreur, on reste sur les données actuelles
    });
  }, [useMockData, fetchRequests, setRequests, toast]);

  // Vérifier si l'utilisateur est admin (APRÈS tous les hooks)
  if (user?.role !== 'admin') {
    return <Navigate to="/chat" replace />;
  }

  // Loading initial
  if (isLoading && requests.length === 0) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Spinner size="lg" />
            <p className="text-text-secondary mt-4">Chargement des demandes...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <Header />

      {/* Bannière mode démo */}
      {useMockData && (
        <div className="bg-orange-500/20 border-b border-orange-500/30 px-4 py-2">
          <p className="text-sm text-orange-400 text-center">
            Mode démonstration - API Safeguard non connectée
          </p>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Liste des demandes */}
        <RequestList
          requests={requests}
          selectedRequest={selectedRequest}
          onSelectRequest={setSelectedRequest}
          onRefresh={handleRefresh}
        />

        {/* Main content - Détail de la demande */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {selectedRequest ? (
            <RequestDetail
              request={selectedRequest}
              comment={comment}
              onCommentChange={setComment}
              onApprove={handleApprove}
              onReject={handleReject}
              isLoading={isActionLoading}
            />
          ) : (
            <RequestDetailEmpty />
          )}
        </main>
      </div>
    </div>
  );
}
