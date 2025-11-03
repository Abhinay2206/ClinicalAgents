'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function PageTransition({ children, href }) {
  const router = useRouter();
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleClick = (e) => {
    e.preventDefault();
    setIsTransitioning(true);

    // Wait for animation to complete before navigating
    setTimeout(() => {
      router.push(href);
    }, 800);
  };

  return (
    <>
      <div onClick={handleClick} style={{ display: 'inline-block' }}>
        {children}
      </div>

      <AnimatePresence>
        {isTransitioning && (
          <>
            {/* Smooth Circular Wipe Transition */}
            <motion.div
              initial={{ scale: 0, borderRadius: '50%' }}
              animate={{ 
                scale: 3, 
                borderRadius: '0%',
              }}
              transition={{ 
                duration: 0.6, 
                ease: [0.43, 0.13, 0.23, 0.96] 
              }}
              className="fixed inset-0 z-[100] bg-gradient-to-br from-[#00ADB5] to-[#00C6FF]"
              style={{
                transformOrigin: 'center center',
              }}
            />

            {/* Subtle Particles Effect */}
            {[...Array(15)].map((_, i) => (
              <motion.div
                key={i}
                initial={{
                  x: '50vw',
                  y: '50vh',
                  scale: 0,
                  opacity: 0.8,
                }}
                animate={{
                  x: `${Math.random() * 100}vw`,
                  y: `${Math.random() * 100}vh`,
                  scale: [0, 1.5, 0],
                  opacity: [0.8, 1, 0],
                }}
                transition={{
                  duration: 1,
                  delay: i * 0.02,
                  ease: "easeOut"
                }}
                className="fixed w-1.5 h-1.5 rounded-full bg-white z-[99]"
                style={{
                  pointerEvents: 'none',
                }}
              />
            ))}
          </>
        )}
      </AnimatePresence>
    </>
  );
}
