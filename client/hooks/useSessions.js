'use client';

import { useState, useEffect, useCallback } from 'react';
import { generateId } from '@/utils/idUtils';

export function useSessions() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  // Load sessions from localStorage on mount
  useEffect(() => {
    const savedSessions = localStorage.getItem('clinical-agent-sessions');
    if (savedSessions) {
      try {
        const parsed = JSON.parse(savedSessions);
        setSessions(parsed);
        if (parsed.length > 0) {
          setCurrentSessionId(parsed[0].id);
        }
      } catch (err) {
        console.error('Failed to parse sessions:', err);
        initializeDefaultSession();
      }
    } else {
      initializeDefaultSession();
    }
  }, []);

  // Save sessions to localStorage whenever they change
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem('clinical-agent-sessions', JSON.stringify(sessions));
    }
  }, [sessions]);

  const initializeDefaultSession = () => {
    const defaultSession = {
      id: generateId(),
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setSessions([defaultSession]);
    setCurrentSessionId(defaultSession.id);
  };

  const createNewSession = useCallback(() => {
    const newSession = {
      id: generateId(),
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    return newSession.id;
  }, []);

  const switchSession = useCallback((sessionId) => {
    setCurrentSessionId(sessionId);
  }, []);

  const deleteSession = useCallback((sessionId) => {
    setSessions(prev => {
      const updated = prev.filter(s => s.id !== sessionId);
      
      // If deleting current session, switch to another
      if (sessionId === currentSessionId) {
        if (updated.length > 0) {
          setCurrentSessionId(updated[0].id);
        } else {
          // Create a new session if all deleted
          const newSession = {
            id: generateId(),
            title: 'New Conversation',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };
          setCurrentSessionId(newSession.id);
          return [newSession];
        }
      }
      
      return updated;
    });
  }, [currentSessionId]);

  const updateSessionTitle = useCallback((sessionId, title) => {
    setSessions(prev => prev.map(s => 
      s.id === sessionId 
        ? { ...s, title, updatedAt: new Date().toISOString() }
        : s
    ));
  }, []);

  return {
    sessions,
    currentSessionId,
    createNewSession,
    switchSession,
    deleteSession,
    updateSessionTitle,
  };
}
