'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

export default function RippleEffect() {
  const [ripples, setRipples] = useState([]);

  useEffect(() => {
    const handleClick = (e) => {
      const newRipple = {
        x: e.clientX,
        y: e.clientY,
        id: Date.now() + Math.random(),
      };

      setRipples((prev) => [...prev, newRipple]);

      // Remove ripple after animation
      setTimeout(() => {
        setRipples((prev) => prev.filter((ripple) => ripple.id !== newRipple.id));
      }, 2000);
    };

    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {ripples.map((ripple) => (
        <motion.div
          key={ripple.id}
          className="absolute rounded-full border-2"
          style={{
            left: ripple.x,
            top: ripple.y,
            borderColor: '#00ADB5',
            x: '-50%',
            y: '-50%',
          }}
          initial={{
            width: 0,
            height: 0,
            opacity: 0.8,
          }}
          animate={{
            width: 300,
            height: 300,
            opacity: 0,
          }}
          transition={{
            duration: 1.5,
            ease: 'easeOut',
          }}
        />
      ))}
    </div>
  );
}
