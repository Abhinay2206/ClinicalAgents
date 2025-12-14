'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { chatService } from '@/services/chatService';

export function useChat(sessionId, updateSessionTitle) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  // Load history when session changes
  const loadHistory = useCallback(async (sid) => {
    try {
      setIsLoading(true);
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
      } else {
        // Empty history is OK, just set empty messages
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
      // Show error to user if history loading fails
      setError(`Failed to load chat history: ${err.message}`);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (sessionId) {
      loadHistory(sessionId);
    } else {
      setMessages([]);
    }
  }, [sessionId, loadHistory]);

  const sendMessage = useCallback(async (content, explicitSessionId = null) => {
    if (!content.trim()) return;

    // Use explicit session ID if provided, otherwise use hook's sessionId
    const activeSessionId = explicitSessionId || sessionId;

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

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
      if (newMessages.length === 1 && activeSessionId) {
        // Use smart title generation
        const title = chatService.generateChatTitle(content);

        // Persist title to backend
        chatService.updateSessionTitle(activeSessionId, title)
          .then(() => {
            // Update local state after successful backend update
            if (updateSessionTitle) {
              updateSessionTitle(activeSessionId, title);
            }
          })
          .catch(err => {
            console.error('Failed to update session title:', err);
            // Still update local state even if backend fails
            if (updateSessionTitle) {
              updateSessionTitle(activeSessionId, title);
            }
          });
      }

      return newMessages;
    });

    setIsLoading(true);
    setError(null);

    try {
      const response = await chatService.sendMessage(content, activeSessionId, abortControllerRef.current.signal);

      console.log('📥 Received response from backend:', response);

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

      console.log('✅ Adding assistant message to state:', assistantMessage);
      setMessages(prev => {
        const newMessages = [...prev, assistantMessage];
        console.log('📝 Updated messages array:', newMessages);
        return newMessages;
      });
    } catch (err) {
      // Don't show error if it was an abort
      if (err.name === 'AbortError') {
        console.log('Request cancelled by user');
        return;
      }

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
      abortControllerRef.current = null;
    }
  }, [sessionId, updateSessionTitle]);

  const cancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    cancelRequest,
    clearMessages,
  };
}
