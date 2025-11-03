'use client';

import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

export default function MessageList({ messages, isLoading }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="h-full overflow-y-auto scroll-smooth">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
        {messages.map((message, index) => (
          <MessageBubble key={message.id || index} message={message} />
        ))}
        
        {isLoading && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
