'use client';

import { motion } from 'framer-motion';

export default function ShimmerText({ children, className = '' }) {
  return (
    <motion.span
      className={`relative inline-block ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      {children}
      <motion.span
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
        animate={{
          x: ['-100%', '200%'],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          repeatDelay: 5,
          ease: "easeInOut"
        }}
        style={{
          WebkitMaskImage: 'linear-gradient(90deg, transparent, black, transparent)',
          maskImage: 'linear-gradient(90deg, transparent, black, transparent)',
        }}
      />
    </motion.span>
  );
}
