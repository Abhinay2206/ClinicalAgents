'use client';

import { useState } from 'react';
import { UserCircleIcon } from '@heroicons/react/24/solid';
import { SparklesIcon } from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import PredictionDisplay from './PredictionDisplay';
import { formatTime } from '@/utils/dateUtils';
import { motion } from 'framer-motion';

export default function MessageBubble({ message }) {
  const [showTime, setShowTime] = useState(false);
  const isUser = message.role === 'user';

  // Detect if this is a clinical trial prediction response
  const isPrediction = !isUser && typeof message.content === 'string' && (
    message.content.includes('🎯 Clinical Trial Prediction') ||
    message.content.includes('Clinical Trial Prediction') ||
    (message.content.includes('**Prediction**:') && message.content.includes('**Confidence**:')) ||
    message.content.includes('Agent Reports:')
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} group`}
      onMouseEnter={() => setShowTime(true)}
      onMouseLeave={() => setShowTime(false)}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--accent-teal)] to-[var(--accent-blue)] flex items-center justify-center shadow-lg shadow-[var(--accent-teal)]/20">
            <UserCircleIcon className="w-5 h-5 text-white" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] flex items-center justify-center shadow-sm">
            <SparklesIcon className="w-4.5 h-4.5 text-[var(--accent-teal)]" />
          </div>
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-4xl ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {isPrediction ? (
          /* Render prediction with special component */
          <motion.div
            layout
            className="w-full"
          >
            <PredictionDisplay content={message.content} />

            {/* Timestamp on hover */}
            {showTime && message.timestamp && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="text-xs text-[var(--text-tertiary)] mt-2 px-1 text-left"
              >
                {formatTime(message.timestamp)}
              </motion.div>
            )}
          </motion.div>
        ) : (
          /* Regular message bubble */
          <>
            <motion.div
              layout
              className={`
              px-5 py-3.5 rounded-2xl
              ${isUser
                  ? 'bg-gradient-to-br from-[var(--accent-teal)] to-[var(--accent-blue)] text-white ml-auto rounded-tr-sm shadow-[var(--shadow-glow)]'
                  : 'bg-[var(--bg-tertiary)]/80 backdrop-blur-sm border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-tl-sm shadow-sm'
                }
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
            </motion.div>

            {/* Timestamp on hover */}
            {showTime && message.timestamp && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className={`
                text-xs text-[var(--text-tertiary)] mt-1 px-1
                ${isUser ? 'text-right' : 'text-left'}
              `}>
                {formatTime(message.timestamp)}
              </motion.div>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}
