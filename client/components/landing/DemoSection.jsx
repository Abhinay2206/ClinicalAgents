'use client';

import { motion, useScroll, useTransform } from 'framer-motion';
import { User, Sparkles } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';

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
  const sectionRef = useRef(null);
  
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start']
  });

  const y = useTransform(scrollYProgress, [0, 1], [50, -50]);
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  useEffect(() => {
    messages.forEach((_, index) => {
      setTimeout(() => {
        setVisibleMessages(prev => [...prev, index]);
      }, index * 1200);
    });
  }, []);

  return (
    <section 
      id="demo" 
      ref={sectionRef}
      className="relative py-32 px-4 bg-[var(--bg-secondary)] scroll-mt-20 overflow-hidden"
    >
      {/* Parallax background elements */}
      <motion.div 
        className="absolute top-10 left-10 w-72 h-72 rounded-full bg-[#00C6FF]/5 blur-3xl pointer-events-none"
        style={{ y, opacity }}
      />
      <motion.div 
        className="absolute bottom-10 right-10 w-96 h-96 rounded-full bg-[#00ADB5]/5 blur-3xl pointer-events-none"
        style={{ y: useTransform(scrollYProgress, [0, 1], [-50, 50]), opacity }}
      />
      <div className="max-w-5xl mx-auto relative z-10">
        {/* Section Header with Animated Badge */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-20"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            whileInView={{ opacity: 1, scale: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-[#00C6FF]/10 to-[#00ADB5]/10 border border-[#00C6FF]/20 mb-8 backdrop-blur-sm"
          >
            <motion.span 
              className="w-2 h-2 rounded-full bg-[#00C6FF]"
              animate={{ 
                scale: [1, 1.3, 1],
                opacity: [1, 0.5, 1] 
              }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            />
            <span className="text-sm font-medium text-[var(--accent-teal)] tracking-wide">LIVE DEMO</span>
          </motion.div>
          
          <motion.h2 
            className="text-4xl md:text-6xl font-bold text-[var(--text-primary)] mb-6"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.3 }}
          >
            See it in action
          </motion.h2>
          
          <motion.p 
            className="text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            Experience AI-powered clinical insights
          </motion.p>
        </motion.div>

        {/* Chat Demo with 3D Tilt and Depth */}
        <motion.div
          initial={{ opacity: 0, y: 60, scale: 0.9 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: "-100px" }}
          whileHover={{ 
            scale: 1.01,
            y: -5,
            transition: { type: "spring", stiffness: 300, damping: 30 }
          }}
          transition={{ 
            duration: 0.8,
            ease: [0.22, 1, 0.36, 1]
          }}
          className="relative rounded-3xl bg-[var(--bg-tertiary)]/90 backdrop-blur-xl border border-[var(--border-subtle)] shadow-[0_20px_70px_-15px_rgba(0,173,181,0.3)] p-6 md:p-10"
          style={{ 
            transformStyle: "preserve-3d",
            perspective: "1000px"
          }}
        >
          {/* Glow effect */}
          <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-[#00ADB5]/10 via-transparent to-[#00C6FF]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
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
