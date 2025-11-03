'use client';

import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import WelcomeScreen from './WelcomeScreen';
import ErrorCard from './ErrorCard';

export default function ChatMain({ 
  messages, 
  isLoading, 
  error,
  onSendMessage, 
  onToggleSidebar,
  isSidebarOpen 
}) {
  const hasMessages = messages.length > 0;

  return (
    <div className="flex-1 flex flex-col h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <ChatHeader onToggleSidebar={onToggleSidebar} isSidebarOpen={isSidebarOpen} />

      {/* Messages Area */}
      <div className="flex-1 overflow-hidden">
        {error ? (
          <ErrorCard message={error} onRetry={() => window.location.reload()} />
        ) : hasMessages ? (
          <MessageList messages={messages} isLoading={isLoading} />
        ) : (
          <WelcomeScreen onSendMessage={onSendMessage} />
        )}
      </div>

      {/* Input Area */}
      <ChatInput 
        onSendMessage={onSendMessage} 
        isLoading={isLoading}
        showSuggestions={!hasMessages}
      />
    </div>
  );
}
