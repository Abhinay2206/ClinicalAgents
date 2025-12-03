'use client';

import { useState, useEffect, useCallback } from 'react';
import { chatService } from '@/services/chatService';
import { useAuth } from '@/contexts/AuthContext';

export function useSessions() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // Load sessions from backend when authenticated
  useEffect(() => {
    const loadSessions = async () => {
      if (authLoading) return; // Wait for auth to load

      if (!isAuthenticated) {
        setSessions([]);
        setCurrentSessionId(null);
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const userSessions = await chatService.getSessions();
        setSessions(userSessions);

        // Don't auto-select any session - start with empty chat
        // Users can click on a session to load it, or create a new one
        setCurrentSessionId(null);
      } catch (err) {
        console.error('Failed to load sessions:', err);
        // If loading fails, just set empty state
        setSessions([]);
        setCurrentSessionId(null);
      } finally {
        setIsLoading(false);
      }
    };

    loadSessions();
  }, [isAuthenticated, authLoading]);

  const createNewSession = useCallback(async () => {
    try {
      const newSession = await chatService.createSession('New Chat');
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      return newSession.id;
    } catch (err) {
      console.error('Failed to create session:', err);
      throw err;
    }
  }, []);

  const switchSession = useCallback((sessionId) => {
    setCurrentSessionId(sessionId);
  }, []);

  const deleteSession = useCallback(async (sessionId) => {
    try {
      await chatService.deleteSession(sessionId);

      setSessions(prev => {
        const updated = prev.filter(s => s.id !== sessionId);

        // If deleting current session, switch to another
        if (sessionId === currentSessionId) {
          if (updated.length > 0) {
            setCurrentSessionId(updated[0].id);
          } else {
            // Create a new session if all deleted
            createNewSession();
          }
        }

        return updated;
      });
    } catch (err) {
      console.error('Failed to delete session:', err);
      throw err;
    }
  }, [currentSessionId, createNewSession]);

  const updateSessionTitle = useCallback((sessionId, title) => {
    setSessions(prev => prev.map(s =>
      s.id === sessionId
        ? { ...s, title, updated_at: new Date().toISOString() }
        : s
    ));
  }, []);

  const refreshSessions = useCallback(async () => {
    try {
      const userSessions = await chatService.getSessions();
      setSessions(userSessions);
    } catch (err) {
      console.error('Failed to refresh sessions:', err);
    }
  }, []);

  return {
    sessions,
    currentSessionId,
    isLoading,
    createNewSession,
    switchSession,
    deleteSession,
    updateSessionTitle,
    refreshSessions,
    setCurrentSessionId,
  };
}
