'use client';

import { motion } from 'framer-motion';
import { Sparkles, Zap, TrendingUp, Shield, Activity, Brain, Database, Network } from 'lucide-react';

const floatingIcons = [
  { Icon: Sparkles, delay: 0, duration: 15, x: '10%', y: '20%', color: '#00ADB5' },
  { Icon: Zap, delay: 2, duration: 18, x: '85%', y: '15%', color: '#00C6FF' },
  { Icon: TrendingUp, delay: 1, duration: 20, x: '15%', y: '70%', color: '#00ADB5' },
  { Icon: Shield, delay: 3, duration: 17, x: '80%', y: '75%', color: '#00C6FF' },
  { Icon: Activity, delay: 1.5, duration: 16, x: '5%', y: '50%', color: '#00ADB5' },
  { Icon: Brain, delay: 2.5, duration: 19, x: '90%', y: '45%', color: '#00C6FF' },
  { Icon: Database, delay: 0.5, duration: 17, x: '25%', y: '85%', color: '#00ADB5' },
  { Icon: Network, delay: 3.5, duration: 21, x: '70%', y: '30%', color: '#00C6FF' },
];

export default function FloatingIcons() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {floatingIcons.map(({ Icon, delay, duration, x, y, color }, index) => (
        <motion.div
          key={index}
          className="absolute w-10 h-10 opacity-[0.08]"
          style={{ left: x, top: y, color }}
          animate={{
            y: [0, -40, 0],
            x: [0, 25, -15, 0],
            rotate: [0, 15, -15, 0],
            scale: [1, 1.3, 0.9, 1],
          }}
          transition={{
            duration,
            delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          <Icon className="w-full h-full drop-shadow-lg" />
          
          {/* Glow effect */}
          <motion.div
            className="absolute inset-0 blur-xl -z-10"
            style={{ backgroundColor: color }}
            animate={{
              opacity: [0.1, 0.3, 0.1],
              scale: [1, 1.5, 1],
            }}
            transition={{
              duration: duration / 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        </motion.div>
      ))}
      
      {/* Floating abstract shapes - Enhanced */}
      {[...Array(5)].map((_, i) => (
        <motion.div
          key={`shape-${i}`}
          className="absolute rounded-full border opacity-[0.04]"
          style={{
            left: `${(i * 18 + 8) % 90}%`,
            top: `${(i * 25 + 10) % 85}%`,
            width: 100 + i * 30,
            height: 100 + i * 30,
            borderColor: i % 2 === 0 ? '#00ADB5' : '#00C6FF',
            borderWidth: 2,
          }}
          animate={{
            scale: [1, 1.3, 1],
            rotate: [0, 360],
            opacity: [0.04, 0.12, 0.04],
          }}
          transition={{
            duration: 25 + i * 5,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
      
      {/* Hexagonal grid pattern */}
      {[...Array(6)].map((_, i) => (
        <motion.div
          key={`hex-${i}`}
          className="absolute"
          style={{
            left: `${(i * 16 + 12) % 88}%`,
            top: `${(i * 20 + 15) % 82}%`,
          }}
        >
          <motion.svg
            width="60"
            height="70"
            viewBox="0 0 60 70"
            className="opacity-[0.06]"
            animate={{
              rotate: [0, 120, 240, 360],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 30 + i * 3,
              repeat: Infinity,
              ease: "linear",
            }}
          >
            <polygon
              points="30,5 55,20 55,50 30,65 5,50 5,20"
              fill="none"
              stroke={i % 2 === 0 ? '#00ADB5' : '#00C6FF'}
              strokeWidth="2"
            />
          </motion.svg>
        </motion.div>
      ))}
      
      {/* Dots matrix pattern */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: `radial-gradient(circle, ${floatingIcons[0].color} 1px, transparent 1px)`,
        backgroundSize: '50px 50px',
      }} />
    </div>
  );
}
