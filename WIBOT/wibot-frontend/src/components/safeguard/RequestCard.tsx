import { Clock } from 'lucide-react';
import type { SafeguardRequest } from './types';
import { formatToolName, formatTimeRemaining, getTimeColor } from './types';

interface RequestCardProps {
  request: SafeguardRequest;
  isSelected: boolean;
  onClick: () => void;
}

export function RequestCard({ request, isSelected, onClick }: RequestCardProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full p-3 rounded-lg text-left transition-colors ${
        isSelected
          ? 'bg-accent/20 border border-accent'
          : 'bg-bg-primary hover:bg-bg-primary/80 border border-transparent'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-text-primary truncate">
            {formatToolName(request.tool_name)}
          </p>
          <p className="text-sm text-text-secondary truncate mt-0.5">
            {request.context?.client_name || 'Client inconnu'}
          </p>
        </div>
        <span className={`text-xs font-medium flex items-center ${getTimeColor(request.time_remaining_seconds)}`}>
          <Clock className="w-3 h-3 mr-1" />
          {formatTimeRemaining(request.time_remaining_seconds)}
        </span>
      </div>
      {request.context?.ticket_id && (
        <p className="text-xs text-text-secondary mt-2">
          Ticket #{request.context.ticket_id}
        </p>
      )}
    </button>
  );
}
