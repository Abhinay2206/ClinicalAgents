'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronUp } from 'lucide-react';

export default function IntroAnimation({ onComplete }) {
  const [showSwipeHint, setShowSwipeHint] = useState(false);

  useEffect(() => {
    // Load Unicorn Studio script
    if (!window.UnicornStudio) {
      window.UnicornStudio = { isInitialized: false };
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/gh/hiunicornstudio/unicornstudio.js@v1.4.34/dist/unicornStudio.umd.js';
      script.onload = function() {
        if (!window.UnicornStudio.isInitialized) {
          window.UnicornStudio.init();
          window.UnicornStudio.isInitialized = true;
        }
      };
      (document.head || document.body).appendChild(script);
    }

    // Show swipe hint after 2 seconds
    const hintTimer = setTimeout(() => {
      setShowSwipeHint(true);
    }, 2000);

    // Auto swipe up after 5 seconds
    const autoSwipeTimer = setTimeout(() => {
      onComplete();
    }, 3000);

    // Handle scroll/wheel events to trigger swipe
    const handleScroll = (e) => {
      // Detect upward scroll (negative deltaY) or any scroll attempt
      if (e.deltaY !== 0) {
        onComplete();
      }
    };

    // Handle touch swipe
    let touchStartY = 0;
    const handleTouchStart = (e) => {
      touchStartY = e.touches[0].clientY;
    };

    const handleTouchMove = (e) => {
      const touchEndY = e.touches[0].clientY;
      const deltaY = touchStartY - touchEndY;
      
      // If swiped up more than 50px
      if (deltaY > 50) {
        onComplete();
      }
    };

    // Add event listeners
    window.addEventListener('wheel', handleScroll, { passive: true });
    window.addEventListener('touchstart', handleTouchStart, { passive: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true });

    return () => {
      clearTimeout(hintTimer);
      clearTimeout(autoSwipeTimer);
      window.removeEventListener('wheel', handleScroll);
      window.removeEventListener('touchstart', handleTouchStart);
      window.removeEventListener('touchmove', handleTouchMove);
    };
  }, [onComplete]);

  const handleSwipeUp = () => {
    onComplete();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ 
        y: '-100%',
        opacity: 0
      }}
      transition={{ 
        exit: { 
          duration: 0.8, 
          ease: [0.43, 0.13, 0.23, 0.96] 
        } 
      }}
      className="fixed inset-0 z-50 bg-[var(--bg-primary)] flex items-center justify-center overflow-hidden"
      onClick={handleSwipeUp}
    >
      {/* Unicorn Studio Animation - Full Screen */}
      <div 
        data-us-project="3azaf9r6MqXEQpHPe8hn" 
        style={{ 
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%', 
          height: '100%',
          pointerEvents: 'none'
        }}
      />

      {/* Hide Unicorn Studio Watermark */}
      <style jsx>{`
        [data-us-project] a[href*="unicornstudio"],
        [data-us-project] .us-watermark,
        [data-us-project] [class*="watermark"],
        [data-us-project] [style*="position: absolute"][style*="bottom"],
        [data-us-project] > div > a {
          display: none !important;
          opacity: 0 !important;
          visibility: hidden !important;
        }
      `}</style>

      {/* Swipe Up Hint */}
      <AnimatePresence>
        {showSwipeHint && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3 cursor-pointer"
            onClick={handleSwipeUp}
          >
            {/* Animated Arrow */}
            <motion.div
              animate={{ y: [-5, 5, -5] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              className="w-12 h-12 rounded-full bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] flex items-center justify-center shadow-lg"
            >
              <ChevronUp className="w-6 h-6 text-white" />
            </motion.div>

            {/* Text */}
            <motion.p
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="text-sm text-[var(--text-secondary)] font-medium tracking-wide"
            >
              Scroll, swipe up or click to continue
            </motion.p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Skip Button */}
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        onClick={handleSwipeUp}
        className="absolute top-8 right-8 px-4 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:text-[var(--accent-teal)] hover:bg-[var(--bg-secondary)] transition-all"
      >
        Skip
      </motion.button>
    </motion.div>
  );
}
