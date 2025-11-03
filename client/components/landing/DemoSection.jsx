'use client';

import { motion } from 'framer-motion';
import { User, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';

const messages = [
  {
    role: 'user',
    content: 'What are the enrollment criteria for diabetes trials?'
  },
  {
    role: 'assistant',
    content: 'For Type 2 diabetes trials, typical inclusion criteria include age range 18-75, HbA1c between 7-10%, BMI below 35, and documented diagnosis for at least 6 months. Exclusion criteria often include severe complications, recent cardiovascular events, and certain medications.'
  }
];

export default function DemoSection() {
  const [visibleMessages, setVisibleMessages] = useState([]);

  useEffect(() => {
    messages.forEach((_, index) => {
      setTimeout(() => {
        setVisibleMessages(prev => [...prev, index]);
      }, index * 1200);
    });
  }, []);

  return (
    <section id="demo" className="py-24 px-4 bg-[var(--bg-secondary)] scroll-mt-20">
      <div className="max-w-5xl mx-auto">
        {/* Section Header with Animated Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#00C6FF]/5 border border-[#00C6FF]/10 mb-8"
          >
            <motion.span 
              className="w-1.5 h-1.5 rounded-full bg-[#00C6FF]"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            />
            <span className="text-xs font-medium text-[var(--accent-teal)] tracking-wide">LIVE DEMO</span>
          </motion.div>
          <h2 className="text-4xl md:text-5xl font-bold text-[var(--text-primary)] mb-4">
            See it in action
          </h2>
          <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto">
            Experience AI-powered clinical insights
          </p>
        </motion.div>

        {/* Chat Demo with 3D Tilt */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          whileHover={{ 
            scale: 1.02,
            rotateX: 2,
            rotateY: 2,
          }}
          transition={{ 
            duration: 0.6,
            hover: { type: "spring", stiffness: 300, damping: 30 }
          }}
          className="rounded-2xl bg-[var(--bg-tertiary)]/80 backdrop-blur-xl border border-[var(--border-subtle)] shadow-2xl p-6 md:p-8"
        >
          <div className="space-y-6">
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: message.role === 'user' ? 20 : -20 }}
                animate={visibleMessages.includes(index) ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.5 }}
                className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div className="flex-shrink-0">
                  {message.role === 'user' ? (
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] flex items-center justify-center">
                      <User className="w-5 h-5 text-white" />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-[var(--text-primary)] flex items-center justify-center">
                      <Sparkles className="w-5 h-5 text-[var(--bg-primary)]" />
                    </div>
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  className={`
                    flex-1 max-w-2xl px-5 py-4 rounded-2xl
                    ${message.role === 'user'
                      ? 'bg-gradient-to-r from-[#00ADB5] to-[#00C6FF] text-white ml-auto shadow-lg'
                      : 'bg-[var(--bg-secondary)] text-[var(--text-primary)] shadow-[var(--shadow-soft)]'
                    }
                  `}
                >
                  <p className="text-[15px] leading-relaxed">{message.content}</p>
                </div>
              </motion.div>
            ))}

            {/* Typing Indicator */}
            {visibleMessages.length === messages.length && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.5 }}
                className="text-xs text-[var(--text-tertiary)] text-center"
              >
                AI-powered insights • Real-time analysis
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
