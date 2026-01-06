import { create } from 'zustand';
import type { SafeguardRequest } from '../components/safeguard/types';
import {
  getSafeguardRequests,
  approveSafeguardRequest,
  rejectSafeguardRequest,
} from '../services/safeguard';

interface SafeguardState {
  // Data
  requests: SafeguardRequest[];
  selectedRequest: SafeguardRequest | null;
  pendingCount: number;

  // Loading states
  isLoading: boolean;
  isActionLoading: boolean;
  error: string | null;

  // Polling
  pollingInterval: number;
  isPollingEnabled: boolean;

  // Actions
  setRequests: (requests: SafeguardRequest[]) => void;
  setSelectedRequest: (request: SafeguardRequest | null) => void;
  setLoading: (loading: boolean) => void;
  setActionLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setPollingInterval: (interval: number) => void;
  setPollingEnabled: (enabled: boolean) => void;

  // Async actions
  fetchRequests: (showLoading?: boolean) => Promise<void>;
  approveRequest: (approvalId: string, comment?: string) => Promise<boolean>;
  rejectRequest: (approvalId: string, comment?: string) => Promise<boolean>;
}

export const useSafeguardStore = create<SafeguardState>((set, get) => ({
  // Initial state
  requests: [],
  selectedRequest: null,
  pendingCount: 0,
  isLoading: false,
  isActionLoading: false,
  error: null,
  pollingInterval: 30000, // 30 secondes par défaut
  isPollingEnabled: true,

  // Setters
  setRequests: (requests) => {
    const pendingCount = requests.filter(r => r.status === 'pending').length;
    set({ requests, pendingCount });
  },

  setSelectedRequest: (request) => set({ selectedRequest: request }),

  setLoading: (loading) => set({ isLoading: loading }),

  setActionLoading: (loading) => set({ isActionLoading: loading }),

  setError: (error) => set({ error }),

  setPollingInterval: (interval) => set({ pollingInterval: interval }),

  setPollingEnabled: (enabled) => set({ isPollingEnabled: enabled }),

  // Async: Fetch requests
  fetchRequests: async (showLoading = true) => {
    const state = get();
    if (showLoading) set({ isLoading: true });
    set({ error: null });

    try {
      const response = await getSafeguardRequests('pending');
      if (response.success) {
        const pendingCount = response.requests.filter(r => r.status === 'pending').length;

        // Mettre à jour la demande sélectionnée si elle existe encore
        let selectedRequest = state.selectedRequest;
        if (selectedRequest) {
          const updated = response.requests.find(
            r => r.approval_id === selectedRequest!.approval_id
          );
          selectedRequest = updated || null;
        }

        set({
          requests: response.requests,
          pendingCount,
          selectedRequest,
          isLoading: false,
        });
      } else {
        set({
          error: 'Erreur lors du chargement des demandes',
          isLoading: false,
        });
        throw new Error('API returned success: false');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      let displayError = 'Erreur lors du chargement des demandes';

      if (errorMessage.includes('401')) {
        displayError = 'Accès non autorisé';
      } else if (errorMessage.includes('403')) {
        displayError = "Niveau d'accréditation insuffisant";
      }

      set({
        error: displayError,
        isLoading: false,
      });
      console.error('Safeguard fetch error:', err);
      // Re-throw pour que le composant puisse utiliser le fallback mock data
      throw err;
    }
  },

  // Async: Approve request
  approveRequest: async (approvalId, comment) => {
    set({ isActionLoading: true, error: null });

    try {
      const response = await approveSafeguardRequest({
        approval_id: approvalId,
        comment,
      });

      if (response.success) {
        // Rafraîchir et désélectionner
        await get().fetchRequests(false);
        set({ selectedRequest: null, isActionLoading: false });
        return true;
      } else {
        set({
          error: response.message || "Erreur lors de l'approbation",
          isActionLoading: false,
        });
        return false;
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      set({
        error: `Erreur: ${errorMessage}`,
        isActionLoading: false,
      });
      console.error('Approve error:', err);
      return false;
    }
  },

  // Async: Reject request
  rejectRequest: async (approvalId, comment) => {
    set({ isActionLoading: true, error: null });

    try {
      const response = await rejectSafeguardRequest({
        approval_id: approvalId,
        comment,
      });

      if (response.success) {
        // Rafraîchir et désélectionner
        await get().fetchRequests(false);
        set({ selectedRequest: null, isActionLoading: false });
        return true;
      } else {
        set({
          error: response.message || 'Erreur lors du refus',
          isActionLoading: false,
        });
        return false;
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      set({
        error: `Erreur: ${errorMessage}`,
        isActionLoading: false,
      });
      console.error('Reject error:', err);
      return false;
    }
  },
}));
