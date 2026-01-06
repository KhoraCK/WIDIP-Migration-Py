import { memo } from 'react';
import { User, Bot } from 'lucide-react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { formatMessageTime } from '../../utils/date';
import type { Message as MessageType } from '../../types';

interface MessageProps {
  message: MessageType;
}

export const Message = memo(function Message({ message }: MessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`
        flex gap-4 p-6 animate-message-appear
        ${isUser ? 'bg-bg-user-msg' : 'bg-bg-assistant-msg'}
      `}
    >
      {/* Avatar */}
      <div
        className={`
          w-8 h-8 rounded-full flex-shrink-0
          flex items-center justify-center
          transition-transform hover:scale-110
          ${isUser ? 'bg-accent' : 'bg-green-600'}
        `}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          <span className="font-medium text-text-primary">
            {isUser ? 'Vous' : 'WIBOT'}
          </span>
          <span className="text-xs text-text-secondary">
            {formatMessageTime(message.created_at)}
          </span>
        </div>

        {/* Message content */}
        <div className="text-text-primary">
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </div>
      </div>
    </div>
  );
});
