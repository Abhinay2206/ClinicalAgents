'use client';

import { useState, useEffect } from 'react';
import ChatSidebar from './ChatSidebar';
import ChatMain from './ChatMain';
import { useChat } from '@/hooks/useChat';
import { useSessions } from '@/hooks/useSessions';

export default function ChatInterface() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { sessions, currentSessionId, createNewSession, switchSession, deleteSession } = useSessions();
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat(currentSessionId);

  const handleNewChat = () => {
    const newSessionId = createNewSession();
    clearMessages();
  };

  const handleSessionSwitch = (sessionId) => {
    switchSession(sessionId);
  };

  const handleDeleteSession = (sessionId) => {
    deleteSession(sessionId);
  };

  useEffect(() => {
    // Set sidebar open by default on desktop
    const isDesktop = window.innerWidth >= 1024;
    setIsSidebarOpen(isDesktop);
  }, []);

  return (
    <div className="flex h-screen bg-[var(--bg-primary)] overflow-hidden">
      {/* Sidebar */}
      <ChatSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onNewChat={handleNewChat}
        onSessionSelect={handleSessionSwitch}
        onDeleteSession={handleDeleteSession}
      />

      {/* Main Chat Area */}
      <ChatMain
        messages={messages}
        isLoading={isLoading}
        error={error}
        onSendMessage={sendMessage}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        isSidebarOpen={isSidebarOpen}
      />
    </div>
  );
}
