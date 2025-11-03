'use client';

import { PlusIcon, TrashIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import { formatDistanceToNow } from '@/utils/dateUtils';

export default function ChatSidebar({ 
  isOpen, 
  onClose, 
  sessions, 
  currentSessionId,
  onNewChat,
  onSessionSelect,
  onDeleteSession 
}) {
  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden animate-fade-in"
          onClick={onClose}
        />
      )}
      
      {/* Compact Sidebar */}
      <div className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-58 bg-[var(--bg-tertiary)] border-r border-[var(--border-subtle)]
        transform transition-all duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col
      `}>
        {/* Logo Section */}
        <div className="px-4 py-4 flex items-center gap-2.5 border-b border-[var(--border-subtle)]">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent-teal)] flex items-center justify-center">
            <svg className="w-4.5 h-4.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h1 className="text-[15px] font-semibold text-[var(--text-primary)] tracking-tight">
            ClinicalAgent
          </h1>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={onNewChat}
            className="w-full px-3.5 py-2.5 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--accent-teal)] hover:text-white text-[var(--text-primary)] text-sm font-medium transition-all duration-200 hover:shadow-[var(--shadow-soft)] flex items-center justify-center gap-2"
          >
            <PlusIcon className="w-4.5 h-4.5" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Conversation History */}
        <div className="flex-1 overflow-y-auto p-3">
          <h3 className="text-[11px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-2 px-2">
            Recent
          </h3>
          {sessions.length === 0 ? (
            <div className="text-center py-12 px-2 fade-in">
              <ChatBubbleLeftRightIcon className="w-10 h-10 mx-auto mb-2 text-[var(--text-tertiary)] opacity-30" />
              <p className="text-xs text-[var(--text-tertiary)]">No chats</p>
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map((session, index) => (
                <div
                  key={session.id}
                  className={`
                    group relative px-3 py-2 rounded-lg cursor-pointer fade-in
                    transition-all duration-150
                    ${session.id === currentSessionId 
                      ? 'bg-[var(--bg-secondary)]' 
                      : 'hover:bg-[var(--bg-secondary)]'
                    }
                  `}
                  style={{ animationDelay: `${index * 20}ms` }}
                  onClick={() => onSessionSelect(session.id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--text-primary)] truncate leading-tight">
                        {session.title || 'New Chat'}
                      </p>
                      <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
                        {formatDistanceToNow(session.createdAt)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--bg-primary)] transition-all"
                    >
                      <TrashIcon className="w-3.5 h-3.5 text-[var(--text-tertiary)] hover:text-red-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer Status */}
        <div className="p-3 border-t border-[var(--border-subtle)]">
          <div className="flex items-center gap-2 px-2.5 py-2 rounded-lg bg-[var(--bg-secondary)]">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-xs text-[var(--text-tertiary)]">1 Issue</span>
          </div>
        </div>
      </div>
    </>
  );
}
