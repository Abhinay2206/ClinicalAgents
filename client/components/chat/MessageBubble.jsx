'use client';

import { useState } from 'react';
import { UserCircleIcon } from '@heroicons/react/24/solid';
import { SparklesIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import PredictionDisplay from './PredictionDisplay';
import { formatTime } from '@/utils/dateUtils';
import { motion, AnimatePresence } from 'framer-motion';

export default function MessageBubble({ message }) {
  const [showTime, setShowTime] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
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
            <div className="w-full">
              {/* Collapsible Header for Assistant Messages */}
              {!isUser && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="flex items-center gap-2 mb-2 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors group/toggle"
                >
                  <ChevronDownIcon
                    className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-0' : '-rotate-90'}`}
                  />
                  <span className="font-medium">
                    {isExpanded ? 'Collapse response' : 'Expand response'}
                  </span>
                </button>
              )}

              {/* Message Content with Animation */}
              <AnimatePresence initial={false}>
                {(isUser || isExpanded) && (
                  <motion.div
                    initial={!isUser ? { opacity: 0, height: 0 } : false}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                  >
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
                          : `[&>p]:text-[var(--text-primary)] 
                             [&>ul]:text-[var(--text-secondary)] 
                             [&>ol]:text-[var(--text-secondary)]
                             [&>h1]:text-[var(--text-primary)] [&>h1]:text-xl [&>h1]:font-bold [&>h1]:mb-3 [&>h1]:mt-4
                             [&>h2]:text-[var(--text-primary)] [&>h2]:text-lg [&>h2]:font-semibold [&>h2]:mb-2 [&>h2]:mt-3
                             [&>h3]:text-[var(--text-primary)] [&>h3]:text-base [&>h3]:font-semibold [&>h3]:mb-2 [&>h3]:mt-2
                             [&>h4]:text-[var(--text-secondary)] [&>h4]:text-sm [&>h4]:font-semibold [&>h4]:mb-1.5 [&>h4]:mt-2
                             [&>strong]:text-[var(--accent-teal)] [&>strong]:font-semibold
                             [&>em]:text-[var(--text-secondary)] [&>em]:italic`
                        }
                        [&>p]:leading-relaxed [&>p]:mb-3 [&>p]:last:mb-0
                        [&>ul]:my-3 [&>ul]:space-y-1.5 [&>ul]:pl-5
                        [&>ol]:my-3 [&>ol]:space-y-1.5 [&>ol]:pl-5
                        [&>li]:leading-relaxed 
                        [&>ul>li]:list-disc [&>ul>li]:marker:text-[var(--accent-teal)]
                        [&>ol>li]:list-decimal [&>ol>li]:marker:text-[var(--accent-teal)] [&>ol>li]:marker:font-semibold
                        [&>pre]:bg-[var(--bg-primary)] [&>pre]:rounded-lg [&>pre]:p-3 [&>pre]:my-3 [&>pre]:border [&>pre]:border-[var(--border-subtle)]
                        [&>code]:text-sm [&>code]:font-mono [&>code]:text-[var(--accent-teal)] [&>code]:bg-[var(--bg-primary)]/50 [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded
                        [&>blockquote]:border-l-4 [&>blockquote]:border-[var(--accent-teal)] [&>blockquote]:pl-4 [&>blockquote]:py-1 [&>blockquote]:my-3 [&>blockquote]:italic [&>blockquote]:text-[var(--text-secondary)]
                        [&>hr]:border-[var(--border-subtle)] [&>hr]:my-4
                        [&>table]:w-full [&>table]:my-4 [&>table]:border-collapse
                        [&>table>thead]:bg-[var(--bg-secondary)]
                        [&>table>thead>tr>th]:px-3 [&>table>thead>tr>th]:py-2 [&>table>thead>tr>th]:text-left [&>table>thead>tr>th]:font-semibold [&>table>thead>tr>th]:text-[var(--text-primary)] [&>table>thead>tr>th]:border-b [&>table>thead>tr>th]:border-[var(--border-subtle)]
                        [&>table>tbody>tr>td]:px-3 [&>table>tbody>tr>td]:py-2 [&>table>tbody>tr>td]:border-b [&>table>tbody>tr>td]:border-[var(--border-subtle)]/50
                        [&>table>tbody>tr:hover]:bg-[var(--bg-secondary)]/30
                      `}>
                        {typeof message.content === 'string' ? (
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              // Custom components for better rendering
                              h1: ({ node, ...props }) => <h1 className="first:mt-0" {...props} />,
                              h2: ({ node, ...props }) => <h2 className="first:mt-0" {...props} />,
                              h3: ({ node, ...props }) => <h3 className="first:mt-0" {...props} />,
                              h4: ({ node, ...props }) => <h4 className="first:mt-0" {...props} />,
                              p: ({ node, ...props }) => <p className="first:mt-0" {...props} />,
                              ul: ({ node, ...props }) => <ul className="first:mt-0" {...props} />,
                              ol: ({ node, ...props }) => <ol className="first:mt-0" {...props} />,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        ) : (
                          <p>{message.content}</p>
                        )}
                      </div>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

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
