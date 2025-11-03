'use client';

import { useState } from 'react';
import { UserCircleIcon } from '@heroicons/react/24/solid';
import { SparklesIcon } from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatTime } from '@/utils/dateUtils';

export default function MessageBubble({ message }) {
  const [showTime, setShowTime] = useState(false);
  const isUser = message.role === 'user';

  return (
    <div 
      className={`flex gap-3 fade-in ${isUser ? 'flex-row-reverse' : 'flex-row'} group`}
      onMouseEnter={() => setShowTime(true)}
      onMouseLeave={() => setShowTime(false)}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-[var(--accent-teal)] flex items-center justify-center">
            <UserCircleIcon className="w-5 h-5 text-white" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-[var(--text-primary)] flex items-center justify-center">
            <SparklesIcon className="w-4.5 h-4.5 text-[var(--bg-primary)]" />
          </div>
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-2xl ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className={`
          px-4 py-3 rounded-xl
          ${isUser 
            ? 'bg-[var(--accent-teal)] text-white ml-auto' 
            : 'bg-[var(--bg-secondary)] text-[var(--text-primary)]'
          }
          shadow-[var(--shadow-soft)]
          max-w-full
        `}>
          {/* Message Text */}
          <div className={`
            prose prose-sm max-w-none
            ${isUser 
              ? 'prose-invert [&>p]:text-white [&>ul]:text-white [&>ol]:text-white' 
              : '[&>p]:text-[var(--text-primary)] [&>ul]:text-[var(--text-primary)] [&>ol]:text-[var(--text-primary)]'
            }
            [&>p]:leading-relaxed [&>p]:m-0
            [&>ul]:my-2 [&>ol]:my-2
            [&>li]:my-1
            [&>pre]:bg-[var(--bg-primary)] [&>pre]:rounded-lg [&>pre]:p-3 [&>pre]:my-2
            [&>code]:text-sm [&>code]:font-mono
            [&>blockquote]:border-l-2 [&>blockquote]:border-[var(--accent-teal)] [&>blockquote]:pl-3 [&>blockquote]:italic
          `}>
            {typeof message.content === 'string' ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            ) : (
              <p>{message.content}</p>
            )}
          </div>
        </div>

        {/* Timestamp on hover */}
        {showTime && message.timestamp && (
          <div className={`
            text-xs text-[var(--text-tertiary)] mt-1 px-1 fade-in
            ${isUser ? 'text-right' : 'text-left'}
          `}>
            {formatTime(message.timestamp)}
          </div>
        )}
      </div>
    </div>
  );
}
