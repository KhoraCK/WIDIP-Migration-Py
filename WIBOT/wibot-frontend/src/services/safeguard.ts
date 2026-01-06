import api from './api';
import type { SafeguardRequest, ApprovalStatus } from '../components/safeguard/types';

// ============================================
// SAFEGUARD API TYPES
// ============================================

export interface SafeguardListResponse {
  success: boolean;
  requests: SafeguardRequest[];
  total: number;
}

export interface SafeguardDetailResponse {
  success: boolean;
  request: SafeguardRequest;
}

export interface SafeguardActionResponse {
  success: boolean;
  approval_id: string;
  status: ApprovalStatus;
  message: string;
}

export interface SafeguardApproveRequest {
  approval_id: string;
  comment?: string;
}

export interface SafeguardRejectRequest {
  approval_id: string;
  comment?: string;
}

// ============================================
// SAFEGUARD API FUNCTIONS
// ============================================

/**
 * Récupère la liste des demandes Safeguard en attente
 */
export async function getSafeguardRequests(
  status: ApprovalStatus = 'pending'
): Promise<SafeguardListResponse> {
  const response = await api.get<SafeguardListResponse>('/webhook/wibot/safeguard/requests', {
    params: { status }
  });
  return response.data;
}

/**
 * Récupère les détails d'une demande spécifique
 */
export async function getSafeguardRequestDetail(
  approvalId: string
): Promise<SafeguardDetailResponse> {
  const response = await api.get<SafeguardDetailResponse>(
    `/webhook/wibot/safeguard/request/${approvalId}`
  );
  return response.data;
}

/**
 * Approuve une demande Safeguard
 */
export async function approveSafeguardRequest(
  data: SafeguardApproveRequest
): Promise<SafeguardActionResponse> {
  const response = await api.post<SafeguardActionResponse>(
    '/webhook/wibot/safeguard/approve',
    data
  );
  return response.data;
}

/**
 * Rejette une demande Safeguard
 */
export async function rejectSafeguardRequest(
  data: SafeguardRejectRequest
): Promise<SafeguardActionResponse> {
  const response = await api.post<SafeguardActionResponse>(
    '/webhook/wibot/safeguard/reject',
    data
  );
  return response.data;
}

/**
 * Récupère l'historique des demandes traitées
 */
export async function getSafeguardHistory(
  limit: number = 50
): Promise<SafeguardListResponse> {
  const response = await api.get<SafeguardListResponse>('/webhook/wibot/safeguard/history', {
    params: { limit }
  });
  return response.data;
}
