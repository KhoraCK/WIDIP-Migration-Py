import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getSafeguardRequests,
  approveSafeguardRequest,
  rejectSafeguardRequest,
} from '../services/safeguard';
import type { SafeguardRequest } from '../components/safeguard/types';

interface UseSafeguardOptions {
  /** Intervalle de polling en ms (défaut: 30000 = 30s) */
  pollingInterval?: number;
  /** Activer le polling automatique */
  enablePolling?: boolean;
}

interface UseSafeguardReturn {
  requests: SafeguardRequest[];
  selectedRequest: SafeguardRequest | null;
  selectRequest: (request: SafeguardRequest | null) => void;
  isLoading: boolean;
  isActionLoading: boolean;
  error: string | null;
  refresh: () => void;
  approve: (approvalId: string, comment?: string) => Promise<boolean>;
  reject: (approvalId: string, comment?: string) => Promise<boolean>;
}

export function useSafeguard(options: UseSafeguardOptions = {}): UseSafeguardReturn {
  const { pollingInterval = 30000, enablePolling = true } = options;

  const [requests, setRequests] = useState<SafeguardRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<SafeguardRequest | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollingRef = useRef<number | null>(null);

  // Fetch des demandes
  const fetchRequests = useCallback(async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    setError(null);

    try {
      const response = await getSafeguardRequests('pending');
      if (response.success) {
        setRequests(response.requests);

        // Mettre à jour la demande sélectionnée si elle existe encore
        if (selectedRequest) {
          const updatedRequest = response.requests.find(
            r => r.approval_id === selectedRequest.approval_id
          );
          if (updatedRequest) {
            setSelectedRequest(updatedRequest);
          } else {
            // La demande a été traitée ou a expiré
            setSelectedRequest(null);
          }
        }
      } else {
        setError('Erreur lors du chargement des demandes');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      if (errorMessage.includes('401')) {
        setError('Accès non autorisé');
      } else if (errorMessage.includes('403')) {
        setError('Niveau d\'accréditation insuffisant');
      } else {
        setError('Erreur lors du chargement des demandes');
      }
      console.error('Safeguard fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedRequest]);

  // Chargement initial
  useEffect(() => {
    fetchRequests();
  }, []);

  // Polling automatique
  useEffect(() => {
    if (enablePolling && pollingInterval > 0) {
      pollingRef.current = window.setInterval(() => {
        fetchRequests(false); // Sans indicateur de chargement
      }, pollingInterval);
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [enablePolling, pollingInterval, fetchRequests]);

  // Sélection d'une demande
  const selectRequest = useCallback((request: SafeguardRequest | null) => {
    setSelectedRequest(request);
  }, []);

  // Approuver une demande
  const approve = useCallback(async (approvalId: string, comment?: string): Promise<boolean> => {
    setIsActionLoading(true);
    setError(null);

    try {
      const response = await approveSafeguardRequest({ approval_id: approvalId, comment });
      if (response.success) {
        // Rafraîchir la liste et désélectionner
        await fetchRequests(false);
        setSelectedRequest(null);
        return true;
      } else {
        setError(response.message || 'Erreur lors de l\'approbation');
        return false;
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      setError(`Erreur: ${errorMessage}`);
      console.error('Approve error:', err);
      return false;
    } finally {
      setIsActionLoading(false);
    }
  }, [fetchRequests]);

  // Rejeter une demande
  const reject = useCallback(async (approvalId: string, comment?: string): Promise<boolean> => {
    setIsActionLoading(true);
    setError(null);

    try {
      const response = await rejectSafeguardRequest({ approval_id: approvalId, comment });
      if (response.success) {
        // Rafraîchir la liste et désélectionner
        await fetchRequests(false);
        setSelectedRequest(null);
        return true;
      } else {
        setError(response.message || 'Erreur lors du refus');
        return false;
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      setError(`Erreur: ${errorMessage}`);
      console.error('Reject error:', err);
      return false;
    } finally {
      setIsActionLoading(false);
    }
  }, [fetchRequests]);

  return {
    requests,
    selectedRequest,
    selectRequest,
    isLoading,
    isActionLoading,
    error,
    refresh: () => fetchRequests(true),
    approve,
    reject,
  };
}
