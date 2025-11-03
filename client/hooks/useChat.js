'use client';

import { useState, useCallback, useEffect } from 'react';
import { chatService } from '@/services/chatService';

export function useChat(sessionId) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load history when session changes
  useEffect(() => {
    if (sessionId) {
      loadHistory(sessionId);
    } else {
      setMessages([]);
    }
  }, [sessionId]);

  const loadHistory = async (sid) => {
    try {
      const history = await chatService.getHistory(sid);
      if (history && history.messages) {
        setMessages(history.messages);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
      // Don't show error to user for history loading failures
    }
  };

  const sendMessage = useCallback(async (content) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatService.sendMessage(content, sessionId);
      
      // Parse agent response
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response || response.final_response || 'No response received',
        timestamp: new Date().toISOString(),
        agents: response.agents_activated || [],
        metadata: {
          trials_analyzed: response.trials_analyzed,
          confidence: response.confidence,
        },
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message || 'Failed to send message. Please try again.');
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  };
}
