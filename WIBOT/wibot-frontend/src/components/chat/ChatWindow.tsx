import { useEffect, useRef } from 'react';
import { MessageSquare } from 'lucide-react';
import { useChatStore, useConversationsStore } from '../../store';
import { Message } from './Message';
import { Spinner } from '../ui';

export function ChatWindow() {
  const { messages, isLoading } = useChatStore();
  const { currentConversation } = useConversationsStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas quand les messages changent
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Pas de conversation sélectionnée
  if (!currentConversation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-bg-primary">
        <div className="text-center px-4">
          <MessageSquare className="w-16 h-16 text-text-secondary mx-auto mb-4 opacity-50" />
          <h2 className="text-2xl font-bold text-text-primary mb-2">
            Bienvenue sur WIBOT
          </h2>
          <p className="text-text-secondary max-w-md">
            Commencez une nouvelle conversation ou sélectionnez-en une existante dans la barre latérale.
          </p>
        </div>
      </div>
    );
  }

  // Conversation sans messages
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-bg-primary">
        <div className="text-center px-4">
          <MessageSquare className="w-16 h-16 text-accent mx-auto mb-4 opacity-75" />
          <h2 className="text-xl font-bold text-text-primary mb-2">
            Nouvelle conversation
          </h2>
          <p className="text-text-secondary max-w-md">
            Posez votre question ou décrivez ce que vous souhaitez faire.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-bg-primary">
      {/* Messages */}
      <div className="divide-y divide-border">
        {messages.map((message) => (
          <Message key={message.message_id} message={message} />
        ))}
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="flex items-center gap-3 p-6 bg-bg-assistant-msg">
          <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
            <Spinner size="sm" className="border-white border-t-transparent" />
          </div>
          <div className="text-text-secondary">
            WIBOT réfléchit...
          </div>
        </div>
      )}

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  );
}
