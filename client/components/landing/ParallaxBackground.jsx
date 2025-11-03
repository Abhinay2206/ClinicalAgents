'use client';

import { motion, useScroll, useTransform } from 'framer-motion';
import { useEffect, useState } from 'react';

export default function ParallaxBackground() {
  const [isReducedMotion, setIsReducedMotion] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  });
  const { scrollY } = useScroll();

  // Create multiple parallax layers with different speeds
  const y1 = useTransform(scrollY, [0, 1000], [0, 200]);
  const y2 = useTransform(scrollY, [0, 1000], [0, 150]);
  const y3 = useTransform(scrollY, [0, 1000], [0, 100]);
  const y4 = useTransform(scrollY, [0, 1000], [0, 50]);

  const opacity1 = useTransform(scrollY, [0, 500], [1, 0.3]);
  const scale1 = useTransform(scrollY, [0, 500], [1, 1.2]);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = (e) => setIsReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  if (isReducedMotion) {
    return (
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-[#00ADB5]/5 via-transparent to-[#00C6FF]/5" />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Background Layer - Slowest */}
      <motion.div 
        style={{ y: y4 }}
        className="absolute inset-0"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[#00ADB5]/5 via-transparent to-[#00C6FF]/5" />
        
        {/* Animated gradient mesh */}
        <motion.div
          className="absolute inset-0 opacity-20"
          animate={{
            background: [
              'radial-gradient(circle at 20% 50%, rgba(0, 173, 181, 0.1) 0%, transparent 50%)',
              'radial-gradient(circle at 80% 50%, rgba(0, 198, 255, 0.1) 0%, transparent 50%)',
              'radial-gradient(circle at 50% 80%, rgba(0, 173, 181, 0.1) 0%, transparent 50%)',
              'radial-gradient(circle at 20% 50%, rgba(0, 173, 181, 0.1) 0%, transparent 50%)',
            ],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </motion.div>

      {/* Mid-background Layer - Medium speed */}
      <motion.div 
        style={{ y: y3 }}
        className="absolute inset-0"
      >
        {/* Large floating orb - top left */}
        <motion.div
          className="absolute -top-48 -left-48 w-[500px] h-[500px] rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(0, 173, 181, 0.08) 0%, transparent 70%)',
            filter: 'blur(60px)',
          }}
          animate={{
            x: [0, 50, 0],
            y: [0, -30, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        {/* Large floating orb - bottom right */}
        <motion.div
          className="absolute -bottom-48 -right-48 w-[600px] h-[600px] rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(0, 198, 255, 0.06) 0%, transparent 70%)',
            filter: 'blur(70px)',
          }}
          animate={{
            x: [0, -40, 0],
            y: [0, 40, 0],
            scale: [1, 1.15, 1],
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </motion.div>

      {/* Foreground Layer - Faster movement */}
      <motion.div 
        style={{ y: y2 }}
        className="absolute inset-0"
      >
        {/* Medium orb - center left */}
        <motion.div
          className="absolute top-1/3 left-1/4 w-80 h-80 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(0, 173, 181, 0.12) 0%, transparent 70%)',
            filter: 'blur(50px)',
          }}
          animate={{
            x: [0, 60, 0],
            y: [0, -50, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        {/* Medium orb - center right */}
        <motion.div
          className="absolute top-2/3 right-1/3 w-96 h-96 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(0, 198, 255, 0.1) 0%, transparent 70%)',
            filter: 'blur(55px)',
          }}
          animate={{
            x: [0, -50, 0],
            y: [0, 60, 0],
          }}
          transition={{
            duration: 22,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </motion.div>

      {/* Near-foreground Layer - Fastest */}
      <motion.div 
        style={{ y: y1, opacity: opacity1, scale: scale1 }}
        className="absolute inset-0"
      >
        {/* Small accent orbs */}
        <motion.div
          className="absolute top-1/4 right-1/4 w-64 h-64 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(0, 173, 181, 0.15) 0%, transparent 60%)',
            filter: 'blur(40px)',
          }}
          animate={{
            x: [0, 30, 0],
            y: [0, -40, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <motion.div
          className="absolute bottom-1/4 left-1/3 w-72 h-72 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(0, 198, 255, 0.12) 0%, transparent 60%)',
            filter: 'blur(45px)',
          }}
          animate={{
            x: [0, -40, 0],
            y: [0, 50, 0],
            scale: [1, 1.15, 1],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </motion.div>

      {/* Subtle grid overlay */}
      <div 
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `linear-gradient(var(--text-primary) 1px, transparent 1px),
                           linear-gradient(90deg, var(--text-primary) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />
    </div>
  );
}
