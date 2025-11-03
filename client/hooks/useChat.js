'use client';

import { useState, useCallback, useEffect } from 'react';
import { chatService } from '@/services/chatService';

export function useChat(sessionId, updateSessionTitle) {
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
      const data = await chatService.getHistory(sid);
      // Backend returns { session_id, history: [...messages], audit_logs: [...] }
      if (data && data.history && Array.isArray(data.history)) {
        // Transform backend messages to frontend format
        const transformedMessages = data.history.map((msg, idx) => ({
          id: msg._id || `${sid}-${idx}`,
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp,
          agents: msg.agent_outputs?.activated_agents || [],
          metadata: {
            confidence: msg.agent_outputs?.reasoner?.confidence,
            review_status: msg.agent_outputs?.review?.status,
            used_agents: msg.agent_outputs?.reasoner?.used_agents || [],
          },
        }));
        setMessages(transformedMessages);
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
    
    setMessages(prev => {
      const newMessages = [...prev, userMessage];
      
      // If this is the first message, generate and update session title
      if (newMessages.length === 1 && updateSessionTitle && sessionId) {
        // Use smart title generation
        const title = chatService.generateChatTitle(content);
        updateSessionTitle(sessionId, title);
      }
      
      return newMessages;
    });
    
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatService.sendMessage(content, sessionId);
      
      // Parse agent response - backend returns "final_output"
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.final_output || response.response || response.final_response || 'No response received',
        timestamp: new Date().toISOString(),
        agents: response.agent_results?.activated_agents || response.agents_activated || [],
        metadata: {
          trials_analyzed: response.trials_analyzed,
          confidence: response.reasoner?.confidence || response.confidence,
          review_status: response.review?.status,
          used_agents: response.reasoner?.used_agents || [],
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
  }, [sessionId, updateSessionTitle]);

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
