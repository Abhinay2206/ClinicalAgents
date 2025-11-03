'use client';

import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export default function ErrorCard({ message, onRetry }) {
  return (
    <div className="flex items-center justify-center py-8 fade-in">
      <div className="text-center max-w-sm p-6 rounded-xl bg-[var(--bg-secondary)]">
        <div className="w-10 h-10 mx-auto mb-3 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
        </div>
        
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1.5">
          ⚠️ Something went wrong
        </h3>
        
        <p className="text-xs text-[var(--text-secondary)] mb-4">
          {message || 'Unable to process your request. Please try again.'}
        </p>
        
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 rounded-lg bg-[var(--accent-teal)] hover:bg-[var(--accent-teal)]/90 text-white text-xs font-medium transition-all"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}
