// Types pour le module Safeguard

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired' | 'executed';

export interface SafeguardRequest {
  approval_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  security_level: string;
  status: ApprovalStatus;
  created_at: string;
  expires_at: string;
  time_remaining_seconds: number;
  requester_ip?: string;
  context?: {
    ticket_id?: number;
    client_name?: string;
    description?: string;
  };
  approver?: string;
  approval_comment?: string;
}

// Labels pour les outils
export const TOOL_LABELS: Record<string, string> = {
  ad_reset_password: 'Reset mot de passe AD',
  ad_unlock_account: 'Déverrouillage compte AD',
  ad_disable_account: 'Désactivation compte AD',
  ad_enable_account: 'Réactivation compte AD',
  glpi_close_ticket: 'Fermeture ticket GLPI',
  glpi_assign_ticket: 'Assignation ticket',
  glpi_update_ticket_status: 'Changement statut ticket',
};

// Helpers
export function formatToolName(toolName: string): string {
  return TOOL_LABELS[toolName] || toolName;
}

export function formatTimeRemaining(seconds: number): string {
  if (seconds <= 0) return 'Expiré';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}min`;
}

export function getTimeColor(seconds: number): string {
  if (seconds <= 0) return 'text-red-500';
  if (seconds < 10 * 60) return 'text-red-400';
  if (seconds < 20 * 60) return 'text-orange-400';
  return 'text-text-secondary';
}
