'use client';

import { motion } from 'framer-motion';

export default function MorphingBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Animated Gradient Mesh */}
      <motion.div
        className="absolute top-0 left-0 w-full h-full opacity-30"
        animate={{
          background: [
            'radial-gradient(circle at 20% 50%, rgba(0, 173, 181, 0.15) 0%, transparent 50%)',
            'radial-gradient(circle at 80% 50%, rgba(0, 198, 255, 0.15) 0%, transparent 50%)',
            'radial-gradient(circle at 50% 80%, rgba(0, 173, 181, 0.15) 0%, transparent 50%)',
            'radial-gradient(circle at 20% 50%, rgba(0, 173, 181, 0.15) 0%, transparent 50%)',
          ],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Floating Orbs */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(0, 173, 181, 0.1) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
        animate={{
          x: [0, 100, 0],
          y: [0, -50, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      <motion.div
        className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(0, 198, 255, 0.08) 0%, transparent 70%)',
          filter: 'blur(60px)',
        }}
        animate={{
          x: [0, -80, 0],
          y: [0, 60, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(var(--text-primary) 1px, transparent 1px),
                           linear-gradient(90deg, var(--text-primary) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />
    </div>
  );
}
