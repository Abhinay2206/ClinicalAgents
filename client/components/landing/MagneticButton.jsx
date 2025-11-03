'use client';

import { useRef, useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';

export default function MagneticButton({ children, className = '' }) {
  const ref = useRef(null);
  const rafRef = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Check if device is mobile
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768 || 'ontouchstart' in window);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => {
      window.removeEventListener('resize', checkMobile);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (isMobile || !ref.current) return;
    
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }

    rafRef.current = requestAnimationFrame(() => {
      const { clientX, clientY } = e;
      const { left, top, width, height } = ref.current.getBoundingClientRect();
      const x = (clientX - (left + width / 2)) * 0.25; // Reduced intensity
      const y = (clientY - (top + height / 2)) * 0.25;
      setPosition({ x, y });
    });
  }, [isMobile]);

  const handleMouseLeave = useCallback(() => {
    if (isMobile) return;
    setPosition({ x: 0, y: 0 });
  }, [isMobile]);

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={!isMobile ? { x: position.x, y: position.y } : {}}
      transition={{ type: 'spring', stiffness: 150, damping: 15, mass: 0.1 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
