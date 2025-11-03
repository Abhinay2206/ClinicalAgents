'use client';

import { SparklesIcon } from '@heroicons/react/24/outline';

export default function TypingIndicator() {
  return (
    <div className="flex gap-3 fade-in">
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-[var(--text-primary)] flex items-center justify-center">
          <SparklesIcon className="w-4.5 h-4.5 text-[var(--bg-primary)]" />
        </div>
      </div>

      {/* Typing Indicator */}
      <div className="flex-1 max-w-2xl">
        <div className="px-4 py-3 rounded-xl bg-[var(--bg-secondary)] inline-block">
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <div className="w-2 h-2 rounded-full bg-[var(--text-tertiary)] animate-pulse" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-[var(--text-tertiary)] animate-pulse" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-[var(--text-tertiary)] animate-pulse" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm text-[var(--text-secondary)] ml-1">Thinking...</span>
          </div>
        </div>
        
        {/* Shimmer loader underneath */}
        <div className="mt-2 h-0.5 w-28 rounded-full overflow-hidden bg-[var(--bg-secondary)]">
          <div className="h-full shimmer bg-[var(--accent-teal)]"></div>
        </div>
      </div>
    </div>
  );
}
