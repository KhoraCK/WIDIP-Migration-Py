import { Shield, RefreshCw, CheckCircle } from 'lucide-react';
import type { SafeguardRequest } from './types';
import { RequestCard } from './RequestCard';

interface RequestListProps {
  requests: SafeguardRequest[];
  selectedRequest: SafeguardRequest | null;
  onSelectRequest: (request: SafeguardRequest) => void;
  onRefresh: () => void;
}

export function RequestList({
  requests,
  selectedRequest,
  onSelectRequest,
  onRefresh
}: RequestListProps) {
  const pendingRequests = requests.filter(r => r.status === 'pending');

  return (
    <aside className="w-80 bg-bg-secondary border-r border-border flex flex-col">
      {/* Header sidebar */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-accent" />
            <h2 className="font-semibold text-text-primary">Safeguard</h2>
            {pendingRequests.length > 0 && (
              <span className="px-2 py-0.5 text-xs font-medium bg-accent text-white rounded-full">
                {pendingRequests.length}
              </span>
            )}
          </div>
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-bg-primary rounded-lg transition-colors"
            title="Rafraîchir"
          >
            <RefreshCw className="w-4 h-4 text-text-secondary" />
          </button>
        </div>
        <p className="text-sm text-text-secondary mt-1">
          Demandes en attente de validation
        </p>
      </div>

      {/* Liste des demandes */}
      <div className="flex-1 overflow-y-auto">
        {pendingRequests.length === 0 ? (
          <div className="p-8 text-center">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <p className="text-text-primary font-medium">Aucune demande</p>
            <p className="text-sm text-text-secondary mt-1">
              Toutes les demandes ont été traitées
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {pendingRequests.map(request => (
              <RequestCard
                key={request.approval_id}
                request={request}
                isSelected={selectedRequest?.approval_id === request.approval_id}
                onClick={() => onSelectRequest(request)}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
