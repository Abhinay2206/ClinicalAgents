'use client';

import { Bars3Icon } from '@heroicons/react/24/outline';

export default function ChatHeader({ onToggleSidebar, isSidebarOpen }) {

  return (
    <div className="sticky top-0 z-10 bg-[var(--bg-tertiary)]/90 backdrop-blur-xl border-b border-[var(--border-subtle)]">
      <div className="flex items-center justify-between px-5 py-3.5">
        <div className="flex items-center gap-3">
          {!isSidebarOpen && (
            <button
              onClick={onToggleSidebar}
              className="lg:hidden p-2 rounded-lg hover:bg-[var(--bg-secondary)] transition-all duration-150"
            >
              <Bars3Icon className="w-5 h-5 text-[var(--text-primary)]" />
            </button>
          )}
          
          <div className="flex items-center gap-2.5">
            <h1 className="text-base font-semibold text-[var(--text-primary)]">
              ClinicalAgent
            </h1>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--accent-teal)]/10">
              <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-teal)] animate-pulse"></div>
              <span className="text-xs font-medium text-[var(--accent-teal)]">Online</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
