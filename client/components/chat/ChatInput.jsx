'use client';

import { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, StopCircleIcon } from '@heroicons/react/24/solid';

export default function ChatInput({ onSendMessage, onCancelRequest, isLoading }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleStop = () => {
    if (onCancelRequest) {
      onCancelRequest();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestionClick = (text) => {
    setInput(text);
    textareaRef.current?.focus();
  };

  return (
    <div className="border-t border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/90 backdrop-blur-xl">
      <div className="max-w-3xl mx-auto px-3 py-3">
        {/* Input Form */}
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-end gap-2.5 px-4 py-3 rounded-xl bg-[var(--bg-secondary)] focus-within:shadow-[var(--shadow-soft)] transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about clinical trials..."
              rows={1}
              disabled={isLoading}
              className="flex-1 resize-none bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none text-[15px] max-h-32 overflow-y-auto"
              style={{ minHeight: '22px' }}
            />
            {isLoading ? (
              <button
                type="button"
                onClick={handleStop}
                className="flex-shrink-0 w-8 h-8 rounded-lg bg-red-500 hover:bg-red-600 text-white transition-all flex items-center justify-center"
                title="Stop generating"
              >
                <StopCircleIcon className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="flex-shrink-0 w-8 h-8 rounded-lg bg-[var(--accent-teal)] hover:bg-[var(--accent-teal)]/90 disabled:bg-[var(--text-tertiary)] disabled:cursor-not-allowed text-white transition-all flex items-center justify-center"
              >
                <PaperAirplaneIcon className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

        {/* Footer Text */}
        <div className="text-center text-xs text-[var(--text-tertiary)] mt-2.5">
          Powered by Llama 3 · <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] font-mono text-[10px]">↵</kbd> to send
        </div>
      </div>
    </div>
  );
}
