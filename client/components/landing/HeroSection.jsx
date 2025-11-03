'use client';

import { useState } from 'react';
import { motion, useMotionValue, useTransform } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import MagneticButton from './MagneticButton';
import PageTransition from './PageTransition';

export default function HeroSection() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    const { clientX, clientY } = e;
    const { left, top, width, height } = e.currentTarget.getBoundingClientRect();
    const x = (clientX - left - width / 2) / width;
    const y = (clientY - top - height / 2) / height;
    setMousePosition({ x, y });
  };

  return (
    <section 
      className="relative min-h-screen flex items-center justify-center overflow-hidden px-4"
      onMouseMove={handleMouseMove}
    >
      {/* Animated Background with Parallax */}
      <div className="absolute inset-0 opacity-30">
        <motion.div 
          className="absolute inset-0 bg-gradient-to-br from-[#00ADB5]/20 via-transparent to-[#00C6FF]/20"
          style={{
            x: mousePosition.x * 20,
            y: mousePosition.y * 20,
          }}
        ></motion.div>
        <motion.div
          className="absolute top-20 left-20 w-64 h-64 rounded-full bg-[#00ADB5]/10 blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          style={{
            x: mousePosition.x * 50,
            y: mousePosition.y * 50,
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-20 right-20 w-96 h-96 rounded-full bg-[#00C6FF]/10 blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.5, 0.3, 0.5],
          }}
          style={{
            x: mousePosition.x * -40,
            y: mousePosition.y * -40,
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-6xl mx-auto text-center">
        {/* Minimal Floating Icon */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, type: "spring" }}
          className="mb-12 inline-block"
        >
          <motion.div
            className="relative w-14 h-14 mx-auto"
            style={{
              x: mousePosition.x * 10,
              y: mousePosition.y * 10,
            }}
            whileHover={{ scale: 1.15, rotate: 180 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
          >
            {/* Subtle Rotating Ring */}
            <motion.div
              className="absolute inset-0 rounded-full border border-[#00ADB5]/20"
              animate={{ rotate: 360 }}
              transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
            />
            {/* Inner Icon */}
            <motion.div
              className="w-full h-full rounded-full bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] flex items-center justify-center shadow-lg"
              animate={{
                boxShadow: [
                  "0 0 15px rgba(0, 173, 181, 0.2)",
                  "0 0 25px rgba(0, 198, 255, 0.4)",
                  "0 0 15px rgba(0, 173, 181, 0.2)"
                ]
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <Sparkles className="w-6 h-6 text-white" />
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Minimal Headline with Per-Character Magnifying Glass Effect */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.15 }}
          className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6 tracking-tight leading-none relative cursor-default"
        >
          {/* "Clinical" word */}
          <span className="inline-block">
            {'Clinical'.split('').map((char, index) => (
              <motion.span
                key={`clinical-${index}`}
                className="inline-block text-[var(--text-primary)] relative"
                whileHover={{
                  scale: 1.3,
                  y: -5,
                  filter: "brightness(1.3) drop-shadow(0 0 8px rgba(0, 173, 181, 0.5))",
                  zIndex: 10,
                }}
                transition={{
                  type: "spring",
                  stiffness: 500,
                  damping: 20,
                }}
                style={{
                  display: 'inline-block',
                  transformOrigin: 'center center',
                }}
              >
                {char}
              </motion.span>
            ))}
          </span>
          
          {/* "Agent" word with gradient */}
          <span className="inline-block">
            {'Agent'.split('').map((char, index) => (
              <motion.span
                key={`agent-${index}`}
                className="inline-block bg-clip-text text-transparent bg-gradient-to-r from-[#00ADB5] to-[#00C6FF] relative"
                whileHover={{
                  scale: 1.3,
                  y: -5,
                  filter: "brightness(1.4) saturate(1.3) drop-shadow(0 0 12px rgba(0, 198, 255, 0.6))",
                  zIndex: 10,
                }}
                transition={{
                  type: "spring",
                  stiffness: 500,
                  damping: 20,
                }}
                style={{
                  display: 'inline-block',
                  transformOrigin: 'center center',
                  WebkitTextStroke: '0.5px rgba(0, 173, 181, 0.3)',
                }}
              >
                {char}
              </motion.span>
            ))}
          </span>
        </motion.h1>

        {/* Minimal Subtext */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-lg md:text-xl text-[var(--text-secondary)] mb-12 max-w-2xl mx-auto leading-relaxed"
        >
          AI-powered clinical trial intelligence
        </motion.p>

        {/* Minimal CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.45 }}
          className="flex flex-col sm:flex-row gap-3 justify-center items-center"
        >
          <MagneticButton>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <a href="/chat">
                <Button size="lg" className="gap-2 group shadow-lg">
                  Get Started
                  <motion.span
                    animate={{ x: [0, 3, 0] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                  >
                    →
                  </motion.span>
                </Button>
              </a>
            </motion.div>
          </MagneticButton>
          <MagneticButton>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <a href="#demo">
                <Button size="lg" variant="outline" className="backdrop-blur-sm">
                  View Demo
                </Button>
              </a>
            </motion.div>
          </MagneticButton>
        </motion.div>
      </div>

      {/* Scroll Indicator - Outside content div for proper absolute positioning */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 1 }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 z-20"
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-6 h-10 rounded-full border-2 border-[var(--text-tertiary)] flex items-start justify-center p-2"
        >
          <motion.div
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-1.5 h-1.5 rounded-full bg-[var(--accent-teal)]"
          />
        </motion.div>
      </motion.div>
    </section>
  );
}
