import { useState } from 'react';
import { useConversationsStore, useChatStore } from '../store';
import { getConversations, getConversationMessages } from '../services/api';
import type { Conversation } from '../types';

interface UseConversationsReturn {
  isLoading: boolean;
  error: string | null;
  loadConversations: () => Promise<void>;
  createConversation: () => Conversation;
  selectConversation: (conversation: Conversation) => Promise<void>;
}

export function useConversations(): UseConversationsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    setConversations,
    setCurrentConversation,
    addConversation,
  } = useConversationsStore();

  const { setMessages, clearMessages } = useChatStore();

  // Charger toutes les conversations depuis le backend
  // Si aucune conversation, en creer une automatiquement
  // Sinon, selectionner la plus recente
  const loadConversations = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const conversations = await getConversations();
      setConversations(conversations);

      if (conversations.length === 0) {
        // Aucune conversation : en creer une nouvelle automatiquement
        const newConversation: Conversation = {
          conversation_id: crypto.randomUUID(),
          title: 'Nouvelle conversation',
          updated_at: new Date().toISOString(),
          message_count: 0,
        };
        addConversation(newConversation);
        setCurrentConversation(newConversation);
        clearMessages();
      } else {
        // Selectionner la premiere conversation (la plus recente)
        const firstConversation = conversations[0];
        setCurrentConversation(firstConversation);

        // Charger ses messages
        try {
          const messages = await getConversationMessages(firstConversation.conversation_id);
          setMessages(messages);
        } catch {
          clearMessages();
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur de chargement';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // Créer une nouvelle conversation (génère UUID côté client)
  const createConversation = (): Conversation => {
    const newConversation: Conversation = {
      conversation_id: crypto.randomUUID(),
      title: 'Nouvelle conversation',
      updated_at: new Date().toISOString(),
      message_count: 0,
    };

    addConversation(newConversation);
    setCurrentConversation(newConversation);
    clearMessages();

    return newConversation;
  };

  // Sélectionner une conversation et charger ses messages
  const selectConversation = async (conversation: Conversation): Promise<void> => {
    setCurrentConversation(conversation);
    setError(null);

    // Si c'est une nouvelle conversation sans messages, pas besoin d'appeler l'API
    if (conversation.message_count === 0) {
      clearMessages();
      return;
    }

    setIsLoading(true);

    try {
      const messages = await getConversationMessages(conversation.conversation_id);
      setMessages(messages);
    } catch {
      // En cas d'erreur (conversation pas encore en DB), juste vider les messages
      clearMessages();
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    error,
    loadConversations,
    createConversation,
    selectConversation,
  };
}
