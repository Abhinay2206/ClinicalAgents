import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes timeout for chat requests
});

class ChatService {
  async sendMessage(prompt, sessionId = null) {
    try {
      const response = await apiClient.post('/chat', {
        prompt,
        session_id: sessionId,
      });
      
      // Validate response structure
      if (!response.data) {
        throw new Error('Empty response from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Chat service error:', error);
      
      // Better error messages
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout - the server took too long to respond. Please try again.');
      } else if (error.code === 'ERR_NETWORK') {
        throw new Error('Network error - please check if the server is running on port 8000.');
      } else if (error.response) {
        // Server responded with error
        throw new Error(error.response?.data?.detail || `Server error: ${error.response.status}`);
      } else {
        // Client-side error
        throw new Error(error.message || 'An unexpected error occurred');
      }
    }
  }

  async getHistory(sessionId) {
    try {
      const response = await apiClient.get(`/history/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('History service error:', error);
      throw new Error(error.response?.data?.detail || error.message);
    }
  }

  async replaySession(sessionId) {
    try {
      const response = await apiClient.get(`/replay/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Replay service error:', error);
      throw new Error(error.response?.data?.detail || error.message);
    }
  }

  async checkHealth() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check error:', error);
      throw new Error(error.response?.data?.detail || error.message);
    }
  }

  /**
   * Generate a smart title for a conversation based on the first user prompt
   * This creates concise, meaningful titles similar to ChatGPT
   */
  generateChatTitle(firstPrompt) {
    if (!firstPrompt || typeof firstPrompt !== 'string') {
      return 'New Chat';
    }

    const prompt = firstPrompt.trim();
    
    // If prompt is very short, use it as-is
    if (prompt.length <= 40) {
      return prompt;
    }

    // Extract key phrases and create a concise title
    const keywords = this.extractKeywords(prompt);
    
    // If we found good keywords, use them
    if (keywords) {
      return keywords;
    }

    // Fallback: truncate intelligently
    return this.intelligentTruncate(prompt);
  }

  extractKeywords(text) {
    const lowerText = text.toLowerCase();
    
    // Clinical trial specific patterns - order matters!
    const patterns = [
      // Specific trial queries
      { regex: /(?:clinical )?trials? (?:for|about|on|regarding|treating) ([^?.!,]+)/i, prefix: '' },
      { regex: /(?:studies?|research) (?:for|about|on|regarding) ([^?.!,]+)/i, prefix: 'Studies on ' },
      
      // Safety and efficacy questions
      { regex: /(?:safety|efficacy|effectiveness) (?:of|for) ([^?.!,]+)/i, prefix: 'Safety of ' },
      { regex: /side effects? (?:of|for) ([^?.!,]+)/i, prefix: 'Side effects: ' },
      
      // Enrollment questions
      { regex: /(?:how to|can I) (?:enroll|join|participate) (?:in)? ([^?.!,]+)/i, prefix: 'Enrolling in ' },
      { regex: /(?:enrollment|eligibility|requirements?) (?:for|in) ([^?.!,]+)/i, prefix: 'Enrollment: ' },
      
      // Phase questions
      { regex: /phase (\d+) (?:trials?|studies?) (?:for|of|about)? ([^?.!,]+)/i, prefix: 'Phase ' },
      
      // General questions
      { regex: /(?:what|how|when|where|why) (?:is|are|can|does|do) ([^?.!,]+)/i, prefix: '' },
      { regex: /(?:looking for|searching for|find|show me) ([^?.!,]+)/i, prefix: '' },
      
      // Extract drug/condition names (capitalized)
      { regex: /\b([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\b/, prefix: '' },
    ];

    for (const { regex, prefix } of patterns) {
      const match = text.match(regex);
      if (match) {
        let extracted;
        if (match.length > 2 && match[1] && match[2]) {
          // For patterns with two groups (e.g., phase number + condition)
          extracted = `${prefix}${match[1]} ${match[2]}`.trim();
        } else if (match[1]) {
          extracted = `${prefix}${match[1]}`.trim();
        } else {
          continue;
        }
        
        // Clean up and limit length
        extracted = extracted.replace(/\s+/g, ' ').trim();
        
        if (extracted.length > 50) {
          // Try to truncate at word boundary
          const words = extracted.substring(0, 47).split(' ');
          words.pop(); // Remove potentially cut-off word
          extracted = words.join(' ') + '...';
        }
        
        return extracted;
      }
    }

    return null;
  }

  intelligentTruncate(text) {
    // Try to break at a natural point
    const maxLength = 45;
    
    if (text.length <= maxLength) {
      return text;
    }

    // Try to break at sentence boundary
    const sentences = text.match(/[^.!?]+[.!?]+/g);
    if (sentences && sentences[0] && sentences[0].length <= maxLength) {
      return sentences[0].trim();
    }

    // Try to break at word boundary
    const truncated = text.substring(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    
    if (lastSpace > maxLength * 0.7) {
      return truncated.substring(0, lastSpace) + '...';
    }

    return truncated + '...';
  }
}

export const chatService = new ChatService();
