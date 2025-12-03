'use client';

import { useState, useEffect } from 'react';
import ChatSidebar from './ChatSidebar';
import ChatMain from './ChatMain';
import SettingsModal from './SettingsModal';
import ProfileModal from './ProfileModal';
import { useChat } from '@/hooks/useChat';
import { useSessions } from '@/hooks/useSessions';

export default function ChatInterface() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const { sessions, currentSessionId, createNewSession, switchSession, deleteSession, updateSessionTitle } = useSessions();
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat(currentSessionId, updateSessionTitle);

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
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
      />

      {/* Modals */}
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <ProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} />
    </div>
  );
}
