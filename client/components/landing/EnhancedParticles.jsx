'use client';

import { motion } from 'framer-motion';

// Generate static data outside component to avoid impure function calls during render
const particles = Array.from({ length: 30 }, (_, i) => ({
  id: i,
  x: (i * 13.7) % 100,
  y: (i * 23.3) % 100,
  size: (i % 3) + 2,
  duration: 15 + (i % 10),
  delay: (i % 5),
  color: i % 2 === 0 ? '#00ADB5' : '#00C6FF',
}));

const lines = Array.from({ length: 8 }, (_, i) => ({
  id: i,
  x1: (i * 12.5) % 100,
  y1: (i * 15.7) % 100,
  x2: ((i + 1) * 21.3) % 100,
  y2: ((i + 2) * 32.7) % 100,
  color: i % 2 === 0 ? '#00ADB5' : '#00C6FF',
}));

export default function EnhancedParticles() {

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute rounded-full"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: particle.size,
            height: particle.size,
            backgroundColor: particle.color,
          }}
          animate={{
            y: [0, -100, -200, -100, 0],
            x: [0, 20, -20, 10, 0],
            opacity: [0, 0.6, 0.8, 0.6, 0],
            scale: [1, 1.5, 1, 1.2, 1],
          }}
          transition={{
            duration: particle.duration,
            delay: particle.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}

      {/* Larger glowing orbs */}
      {Array.from({ length: 5 }).map((_, i) => (
        <motion.div
          key={`orb-${i}`}
          className="absolute rounded-full blur-xl"
          style={{
            left: `${(i * 23 + 10) % 90}%`,
            top: `${(i * 31 + 15) % 85}%`,
            width: 100 + i * 20,
            height: 100 + i * 20,
            backgroundColor: i % 2 === 0 ? '#00ADB5' : '#00C6FF',
          }}
          animate={{
            y: [0, -50, 0],
            x: [0, 30, 0],
            opacity: [0.05, 0.15, 0.05],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: 15 + i * 3,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: i * 1.5,
          }}
        />
      ))}

      {/* Floating lines/connections */}
      <svg className="absolute inset-0 w-full h-full opacity-10">
        {lines.map((line, i) => (
          <motion.line
            key={`line-${line.id}`}
            x1={`${line.x1}%`}
            y1={`${line.y1}%`}
            x2={`${line.x2}%`}
            y2={`${line.y2}%`}
            stroke={line.color}
            strokeWidth="1"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ 
              pathLength: [0, 1, 0],
              opacity: [0, 0.5, 0],
            }}
            transition={{
              duration: 8 + i,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: i * 0.8,
            }}
          />
        ))}
      </svg>
    </div>
  );
}
