import { useEffect } from 'react';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import { InputBar } from '../components/layout/InputBar';
import { ChatWindow } from '../components/chat/ChatWindow';
import { useConversations } from '../hooks/useConversations';
import { useChat } from '../hooks/useChat';

export function Chat() {
  const { loadConversations } = useConversations();
  const { loadUserTokens } = useChat();

  // Charger les conversations et les tokens au montage
  useEffect(() => {
    loadConversations();
    loadUserTokens();
  }, []);

  return (
    <div className="h-screen flex flex-col bg-bg-primary">
      {/* Header */}
      <Header />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Chat area */}
        <main className="flex-1 flex flex-col">
          {/* Messages area */}
          <ChatWindow />

          {/* Input bar */}
          <InputBar />
        </main>
      </div>
    </div>
  );
}
