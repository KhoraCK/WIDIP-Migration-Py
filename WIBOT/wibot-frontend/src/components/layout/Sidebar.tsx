import { useState } from 'react';
import { Plus, MessageSquare, Pencil, Trash2, Check, X } from 'lucide-react';
import { useConversationsStore } from '../../store';
import { useConversations } from '../../hooks/useConversations';
import { formatRelativeDate } from '../../utils/date';
import { Spinner } from '../ui';
import { renameConversation, deleteConversation } from '../../services/api';
import type { Conversation } from '../../types';

export function Sidebar() {
  const { conversations, currentConversation, updateConversation, removeConversation } = useConversationsStore();
  const { createConversation, selectConversation, isLoading } = useConversations();

  const handleNewConversation = () => {
    createConversation();
  };

  const handleSelectConversation = (conversation: Conversation) => {
    if (conversation.conversation_id !== currentConversation?.conversation_id) {
      selectConversation(conversation);
    }
  };

  const handleRename = async (conversationId: string, newTitle: string) => {
    try {
      const updated = await renameConversation(conversationId, newTitle);
      updateConversation(conversationId, { title: updated.title, updated_at: updated.updated_at });
    } catch (err) {
      console.error('Erreur lors du renommage:', err);
    }
  };

  const handleDelete = async (conversationId: string) => {
    try {
      await deleteConversation(conversationId);
      removeConversation(conversationId);
    } catch (err) {
      console.error('Erreur lors de la suppression:', err);
    }
  };

  return (
    <aside className="w-sidebar bg-bg-secondary border-r border-border flex flex-col h-full">
      {/* Bouton nouvelle conversation */}
      <div className="p-4">
        <button
          onClick={handleNewConversation}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-accent hover:bg-accent-hover text-white rounded-lg font-medium transition-colors"
        >
          <Plus className="w-5 h-5" />
          Nouvelle conversation
        </button>
      </div>

      {/* Liste des conversations */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && conversations.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Spinner size="md" />
          </div>
        ) : conversations.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <MessageSquare className="w-12 h-12 text-text-secondary mx-auto mb-3 opacity-50" />
            <p className="text-text-secondary text-sm">
              Aucune conversation
            </p>
            <p className="text-text-secondary text-xs mt-1">
              Commencez une nouvelle conversation
            </p>
          </div>
        ) : (
          <div className="px-2 pb-4 space-y-1">
            {conversations.map((conversation) => (
              <ConversationItem
                key={conversation.conversation_id}
                conversation={conversation}
                isActive={currentConversation?.conversation_id === conversation.conversation_id}
                onClick={() => handleSelectConversation(conversation)}
                onRename={handleRename}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
  onRename: (conversationId: string, newTitle: string) => Promise<void>;
  onDelete: (conversationId: string) => Promise<void>;
}

function ConversationItem({ conversation, isActive, onClick, onRename, onDelete }: ConversationItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(conversation.title);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditTitle(conversation.title);
    setIsEditing(true);
  };

  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(false);
    setEditTitle(conversation.title);
  };

  const handleConfirmEdit = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (editTitle.trim() && editTitle !== conversation.title) {
      await onRename(conversation.conversation_id, editTitle.trim());
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (editTitle.trim() && editTitle !== conversation.title) {
        onRename(conversation.conversation_id, editTitle.trim());
      }
      setIsEditing(false);
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setEditTitle(conversation.title);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDeleting(true);
  };

  const handleConfirmDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await onDelete(conversation.conversation_id);
    setIsDeleting(false);
  };

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDeleting(false);
  };

  if (isDeleting) {
    return (
      <div className="w-full px-3 py-3 rounded-lg bg-red-500/10 border border-red-500/30">
        <p className="text-sm text-red-400 mb-2">Supprimer cette conversation ?</p>
        <div className="flex gap-2">
          <button
            onClick={handleConfirmDelete}
            className="flex-1 py-1 px-2 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
          >
            Supprimer
          </button>
          <button
            onClick={handleCancelDelete}
            className="flex-1 py-1 px-2 bg-bg-primary hover:bg-bg-primary/80 text-text-secondary text-xs rounded transition-colors"
          >
            Annuler
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className={`
        w-full text-left px-3 py-3 rounded-lg transition-colors cursor-pointer group
        ${isActive
          ? 'bg-bg-primary text-text-primary'
          : 'text-text-secondary hover:bg-bg-primary/50 hover:text-text-primary'
        }
      `}
    >
      <div className="flex items-start gap-3">
        <MessageSquare className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={handleKeyDown}
                autoFocus
                className="flex-1 text-sm bg-bg-secondary border border-border rounded px-2 py-1 text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
              />
              <button
                onClick={handleConfirmEdit}
                className="p-1 text-green-500 hover:text-green-400"
              >
                <Check className="w-4 h-4" />
              </button>
              <button
                onClick={handleCancelEdit}
                className="p-1 text-red-500 hover:text-red-400"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <>
              <p className="text-sm font-medium truncate">
                {conversation.title}
              </p>
              <p className="text-xs text-text-secondary mt-0.5">
                {formatRelativeDate(conversation.updated_at)}
              </p>
            </>
          )}
        </div>
        {!isEditing && (
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleStartEdit}
              className="p-1 text-text-secondary hover:text-accent rounded"
              title="Renommer"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleDeleteClick}
              className="p-1 text-text-secondary hover:text-red-500 rounded"
              title="Supprimer"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
