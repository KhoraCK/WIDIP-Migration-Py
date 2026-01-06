import { useState } from 'react';
import { useChatStore, useConversationsStore } from '../store';
import { sendChatMessage, getUserTokens } from '../services/api';
import type { Message, FileAttachment } from '../types';

interface UseChatReturn {
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string, files?: FileAttachment[]) => Promise<void>;
  loadUserTokens: () => Promise<void>;
}

export function useChat(): UseChatReturn {
  const [error, setError] = useState<string | null>(null);

  const {
    addMessage,
    setLoading,
    isLoading,
    setTokensRemaining,
    chatMode,
  } = useChatStore();

  const {
    currentConversation,
    updateConversation,
  } = useConversationsStore();

  const sendMessage = async (message: string, files?: FileAttachment[]): Promise<void> => {
    if (!currentConversation) {
      setError('Aucune conversation sélectionnée');
      return;
    }

    setLoading(true);
    setError(null);

    // Ajouter le message utilisateur immédiatement
    const userMessage: Message = {
      message_id: Date.now(),
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    addMessage(userMessage);

    try {
      const response = await sendChatMessage({
        conversation_id: currentConversation.conversation_id,
        message,
        mode: chatMode,
        files,
      });

      if (response.success) {
        // Ajouter la réponse de l'assistant
        const assistantMessage: Message = {
          message_id: Date.now() + 1,
          role: 'assistant',
          content: response.response,
          created_at: new Date().toISOString(),
        };
        addMessage(assistantMessage);

        // Mettre à jour les tokens restants
        setTokensRemaining(response.tokens_remaining);

        // Mettre à jour le titre de la conversation si c'est le premier message
        if (currentConversation.message_count === 0) {
          const title = message.length > 50 ? message.substring(0, 50) + '...' : message;
          updateConversation(currentConversation.conversation_id, {
            title,
            message_count: 2,
            updated_at: new Date().toISOString(),
          });
        } else {
          updateConversation(currentConversation.conversation_id, {
            message_count: currentConversation.message_count + 2,
            updated_at: new Date().toISOString(),
          });
        }
      } else {
        setError('Erreur lors de l\'envoi du message');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur de connexion';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Charger les tokens utilisateur depuis le backend
  const loadUserTokens = async (): Promise<void> => {
    try {
      const response = await getUserTokens();
      if (response.success) {
        setTokensRemaining(response.tokens_remaining);
      }
    } catch (err) {
      // Silently fail - on garde la valeur par defaut
      console.warn('Impossible de charger les tokens:', err);
    }
  };

  return {
    isLoading,
    error,
    sendMessage,
    loadUserTokens,
  };
}
