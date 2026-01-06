import { useState, useRef, useEffect, useCallback, type KeyboardEvent } from 'react';
import { Send, Paperclip, X, Code, Zap, FileText } from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import { useConversationsStore, useChatStore } from '../../store';
import { useConversations } from '../../hooks/useConversations';
import { FilePreview } from '../upload/FilePreview';
import { FileDropzone } from '../upload/FileDropzone';
import type { FileAttachment, ChatMode, ChatModeConfig } from '../../types';

// Configuration des modes de chat
const CHAT_MODES: ChatModeConfig[] = [
  { id: 'code', label: 'Code', description: 'Devstral - Optimise pour le code' },
  { id: 'flash', label: 'Flash', description: 'Devstral Small - Rapide et economique' },
  { id: 'redaction', label: 'Pro', description: 'Mistral Large - Qualite maximale' },
];

// Icones pour chaque mode
const MODE_ICONS: Record<ChatMode, typeof Code> = {
  code: Code,
  flash: Zap,
  redaction: FileText,
};

export function InputBar() {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [showDropzone, setShowDropzone] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { sendMessage, isLoading, error } = useChat();
  const { currentConversation } = useConversationsStore();
  const { chatMode, setChatMode } = useChatStore();
  const { createConversation } = useConversations();

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 150);
      textarea.style.height = `${newHeight}px`;
    }
  }, [message]);

  // Lire les fichiers et les convertir en base64
  const readFileAsBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Extraire seulement la partie base64 (sans le prefixe data:...)
        const base64 = result.split(',')[1] || result;
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleSubmit = async () => {
    const trimmedMessage = message.trim();
    if ((!trimmedMessage && files.length === 0) || isLoading) return;

    // Si pas de conversation active, en creer une
    if (!currentConversation) {
      createConversation();
    }

    // Preparer les fichiers
    let fileAttachments: FileAttachment[] | undefined;
    if (files.length > 0) {
      fileAttachments = await Promise.all(
        files.map(async (file) => ({
          name: file.name,
          content: await readFileAsBase64(file),
        }))
      );
    }

    // Reinitialiser le formulaire
    setMessage('');
    setFiles([]);
    setShowDropzone(false);

    // Envoyer le message
    await sendMessage(trimmedMessage || 'Analyse ces fichiers', fileAttachments);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFilesSelected = useCallback((newFiles: File[]) => {
    setFiles((prev) => [...prev, ...newFiles]);
    setShowDropzone(false);
  }, []);

  const handleRemoveFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const canSend = (message.trim().length > 0 || files.length > 0) && !isLoading;

  return (
    <div className="border-t border-border bg-bg-secondary p-4">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Error message */}
        {error && (
          <div className="px-4 py-2 bg-red-500/10 border border-red-500/50 rounded-lg">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* File dropzone (collapsible) */}
        {showDropzone && (
          <div className="relative">
            <button
              onClick={() => setShowDropzone(false)}
              className="absolute -top-2 -right-2 z-10 p-1 bg-bg-secondary border border-border rounded-full text-text-secondary hover:text-text-primary transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
            <FileDropzone onFilesSelected={handleFilesSelected} disabled={isLoading} />
          </div>
        )}

        {/* File preview */}
        {files.length > 0 && (
          <FilePreview files={files} onRemove={handleRemoveFile} disabled={isLoading} />
        )}

        {/* Mode selector */}
        <div className="flex gap-2 justify-center">
          {CHAT_MODES.map((mode) => {
            const Icon = MODE_ICONS[mode.id];
            const isActive = chatMode === mode.id;
            return (
              <button
                key={mode.id}
                onClick={() => setChatMode(mode.id)}
                disabled={isLoading}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all
                  ${isActive
                    ? 'bg-accent text-white'
                    : 'bg-bg-primary text-text-secondary hover:text-text-primary hover:bg-bg-primary/80'
                  }
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
                title={mode.description}
              >
                <Icon className="w-4 h-4" />
                <span>{mode.label}</span>
              </button>
            );
          })}
        </div>

        {/* Input container */}
        <div className="flex gap-3 items-end">
          {/* Attach button */}
          <button
            onClick={() => setShowDropzone(!showDropzone)}
            disabled={isLoading}
            className={`
              p-3 rounded-lg transition-colors
              ${showDropzone
                ? 'bg-accent text-white'
                : 'bg-bg-primary text-text-secondary hover:text-text-primary hover:bg-bg-primary/80'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
            title="Joindre des fichiers"
          >
            <Paperclip className="w-5 h-5" />
          </button>

          {/* Textarea */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Votre message... (Entree pour envoyer, Shift+Entree pour nouvelle ligne)"
              disabled={isLoading}
              rows={1}
              className="
                w-full px-4 py-3
                bg-bg-primary border border-border rounded-lg
                text-text-primary placeholder:text-text-secondary
                resize-none overflow-hidden
                focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                disabled:opacity-50 disabled:cursor-not-allowed
              "
            />
          </div>

          {/* Send button */}
          <button
            onClick={handleSubmit}
            disabled={!canSend}
            className={`
              p-3 rounded-lg transition-colors
              ${canSend
                ? 'bg-accent hover:bg-accent-hover text-white'
                : 'bg-bg-primary text-text-secondary cursor-not-allowed'
              }
            `}
            title="Envoyer (Entree)"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        {/* Helper text with current mode */}
        <p className="text-xs text-text-secondary text-center">
          Mode: {CHAT_MODES.find(m => m.id === chatMode)?.description} | WIBOT peut faire des erreurs.
        </p>
      </div>
    </div>
  );
}
