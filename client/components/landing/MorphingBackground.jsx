'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

export default function MorphingBackground() {
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setIsReducedMotion(mediaQuery.matches);
  }, []);

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Animated Gradient Mesh - Only if not reduced motion */}
      {!isReducedMotion && (
        <motion.div
          className="absolute top-0 left-0 w-full h-full opacity-30 will-change-auto"
          animate={{
            background: [
              'radial-gradient(circle at 20% 50%, rgba(0, 173, 181, 0.15) 0%, transparent 50%)',
              'radial-gradient(circle at 80% 50%, rgba(0, 198, 255, 0.15) 0%, transparent 50%)',
              'radial-gradient(circle at 50% 80%, rgba(0, 173, 181, 0.15) 0%, transparent 50%)',
              'radial-gradient(circle at 20% 50%, rgba(0, 173, 181, 0.15) 0%, transparent 50%)',
            ],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "easeInOut",
            repeatType: "loop",
          }}
        />
      )}

      {/* Floating Orbs - Optimized with GPU acceleration */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full will-change-transform"
        style={{
          background: 'radial-gradient(circle, rgba(0, 173, 181, 0.08) 0%, transparent 70%)',
          filter: 'blur(40px)',
          transform: 'translateZ(0)', // Force GPU acceleration
        }}
        animate={!isReducedMotion ? {
          x: [0, 80, 0],
          y: [0, -40, 0],
          scale: [1, 1.15, 1],
        } : {}}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "easeInOut",
          repeatType: "loop",
        }}
      />

      <motion.div
        className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full will-change-transform"
        style={{
          background: 'radial-gradient(circle, rgba(0, 198, 255, 0.06) 0%, transparent 70%)',
          filter: 'blur(50px)',
          transform: 'translateZ(0)', // Force GPU acceleration
        }}
        animate={!isReducedMotion ? {
          x: [0, -60, 0],
          y: [0, 50, 0],
          scale: [1, 1.1, 1],
        } : {}}
        transition={{
          duration: 35,
          repeat: Infinity,
          ease: "easeInOut",
          repeatType: "loop",
        }}
      />

      {/* Grid Pattern - Static for better performance */}
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
