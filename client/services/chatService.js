const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://0.0.0.0:8000';

class ChatService {
  async sendMessage(prompt, sessionId = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Chat service error:', error);
      throw error;
    }
  }

  async getHistory(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/history/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('History service error:', error);
      throw error;
    }
  }

  async replaySession(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/replay/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Replay service error:', error);
      throw error;
    }
  }

  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  }
}

export const chatService = new ChatService();
