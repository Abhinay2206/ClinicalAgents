'use client';

export default function Error({ error, reset }) {
  return (
    <div className="h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-100 dark:bg-red-900/20">
          <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Something went wrong
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            {error.message || 'An unexpected error occurred'}
          </p>
        </div>

        <button
          onClick={reset}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
