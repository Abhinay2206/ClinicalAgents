'use client';

import { motion } from 'framer-motion';

export default function AnimatedGradientOverlay() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {/* Top gradient waves */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-96 opacity-20"
        style={{
          background: 'linear-gradient(180deg, var(--bg-primary) 0%, transparent 100%)',
        }}
        animate={{
          opacity: [0.15, 0.25, 0.15],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      
      {/* Bottom gradient waves */}
      <motion.div
        className="absolute bottom-0 left-0 right-0 h-96 opacity-20"
        style={{
          background: 'linear-gradient(0deg, var(--bg-primary) 0%, transparent 100%)',
        }}
        animate={{
          opacity: [0.25, 0.15, 0.25],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      
      {/* Animated gradient blobs */}
      <motion.div
        className="absolute top-[20%] left-[10%] w-[500px] h-[500px] rounded-full blur-[120px] opacity-10"
        style={{
          background: 'radial-gradient(circle, #00ADB5 0%, transparent 70%)',
        }}
        animate={{
          x: [0, 100, 0],
          y: [0, -50, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      
      <motion.div
        className="absolute bottom-[20%] right-[10%] w-[600px] h-[600px] rounded-full blur-[130px] opacity-10"
        style={{
          background: 'radial-gradient(circle, #00C6FF 0%, transparent 70%)',
        }}
        animate={{
          x: [0, -80, 0],
          y: [0, 60, 0],
          scale: [1.2, 1, 1.2],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      
      <motion.div
        className="absolute top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full blur-[100px] opacity-[0.07]"
        style={{
          background: 'radial-gradient(circle, #00ADB5 0%, #00C6FF 50%, transparent 100%)',
        }}
        animate={{
          rotate: 360,
          scale: [1, 1.3, 1],
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
      
      {/* Scanline effect */}
      <motion.div
        className="absolute left-0 right-0 h-[2px] opacity-[0.05]"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, #00ADB5 50%, transparent 100%)',
        }}
        animate={{
          top: ['0%', '100%'],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
    </div>
  );
}
