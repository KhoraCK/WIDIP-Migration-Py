import { Shield, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import type { SafeguardRequest } from './types';
import { formatToolName, formatTimeRemaining } from './types';
import { Button } from '../ui';

interface RequestDetailProps {
  request: SafeguardRequest;
  comment: string;
  onCommentChange: (comment: string) => void;
  onApprove: () => void;
  onReject: () => void;
  isLoading: boolean;
}

export function RequestDetail({
  request,
  comment,
  onCommentChange,
  onApprove,
  onReject,
  isLoading
}: RequestDetailProps) {
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="bg-bg-secondary rounded-xl p-6 border border-border">
        {/* En-tête demande */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-accent/20 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-accent" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-text-primary">
                Demande #{request.approval_id}
              </h1>
              <p className="text-text-secondary">
                Niveau requis: <span className="font-medium text-orange-400">{request.security_level}</span>
              </p>
            </div>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
            request.time_remaining_seconds < 10 * 60
              ? 'bg-red-500/20 text-red-400'
              : 'bg-bg-primary text-text-secondary'
          }`}>
            <Clock className="w-4 h-4" />
            <span className="text-sm font-medium">
              Expire dans {formatTimeRemaining(request.time_remaining_seconds)}
            </span>
          </div>
        </div>

        {/* Action demandée */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-text-secondary mb-2">Action demandée</h3>
          <div className="bg-bg-primary rounded-lg p-4">
            <p className="text-lg font-semibold text-text-primary">
              {formatToolName(request.tool_name)}
            </p>
            <div className="mt-2 space-y-1">
              {Object.entries(request.arguments).map(([key, value]) => (
                <p key={key} className="text-sm text-text-secondary">
                  <span className="text-text-primary font-medium">{key}:</span>{' '}
                  {String(value)}
                </p>
              ))}
            </div>
          </div>
        </div>

        {/* Contexte */}
        {request.context && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-text-secondary mb-2">Contexte</h3>
            <div className="bg-bg-primary rounded-lg p-4 space-y-2">
              {request.context.ticket_id && (
                <p className="text-sm">
                  <span className="text-text-secondary">Ticket GLPI:</span>{' '}
                  <span className="text-accent font-medium">#{request.context.ticket_id}</span>
                </p>
              )}
              {request.context.client_name && (
                <p className="text-sm">
                  <span className="text-text-secondary">Client:</span>{' '}
                  <span className="text-text-primary">{request.context.client_name}</span>
                </p>
              )}
              {request.context.description && (
                <p className="text-sm">
                  <span className="text-text-secondary">Description:</span>{' '}
                  <span className="text-text-primary">{request.context.description}</span>
                </p>
              )}
            </div>
          </div>
        )}

        {/* Commentaire */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-text-secondary mb-2">Commentaire (optionnel)</h3>
          <textarea
            value={comment}
            onChange={(e) => onCommentChange(e.target.value)}
            placeholder="Ajouter un commentaire..."
            className="w-full px-4 py-3 bg-bg-primary border border-border rounded-lg text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-accent resize-none"
            rows={3}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <Button
            onClick={onApprove}
            disabled={isLoading}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white"
          >
            <CheckCircle className="w-5 h-5 mr-2" />
            Approuver
          </Button>
          <Button
            onClick={onReject}
            disabled={isLoading}
            variant="secondary"
            className="flex-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 border-red-600/50"
          >
            <XCircle className="w-5 h-5 mr-2" />
            Refuser
          </Button>
        </div>

        {/* Avertissement */}
        <div className="mt-6 p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-orange-400">Action sensible</p>
            <p className="text-sm text-text-secondary mt-1">
              Cette action nécessite une validation humaine car elle peut avoir un impact significatif.
              Veuillez vérifier les informations avant d'approuver.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Composant pour l'état vide (aucune demande sélectionnée)
export function RequestDetailEmpty() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <Shield className="w-16 h-16 text-text-secondary mx-auto mb-4" />
        <p className="text-lg text-text-primary font-medium">Sélectionnez une demande</p>
        <p className="text-text-secondary mt-1">
          Choisissez une demande dans la liste pour voir les détails
        </p>
      </div>
    </div>
  );
}
