'use client';

import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { Activity, HeartPulse, Pill, Microscope } from 'lucide-react';

export default function Hero3DElements() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isMobile, setIsMobile] = useState(false);
  
  // Smooth mouse tracking
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  
  const springConfig = { damping: 25, stiffness: 150 };
  const mouseXSpring = useSpring(mouseX, springConfig);
  const mouseYSpring = useSpring(mouseY, springConfig);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    const handleMouseMove = (e) => {
      if (!isMobile) {
        const { clientX, clientY } = e;
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        
        mouseX.set((clientX - centerX) / centerX);
        mouseY.set((clientY - centerY) / centerY);
        setMousePosition({ x: clientX, y: clientY });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', checkMobile);
    };
  }, [isMobile, mouseX, mouseY]);

  // 3D transforms based on mouse position
  const rotateX = useTransform(mouseYSpring, [-1, 1], [15, -15]);
  const rotateY = useTransform(mouseXSpring, [-1, 1], [-15, 15]);

  // Medical-themed 3D objects
  const cubes = [
    { Icon: HeartPulse, color: '#00ADB5', delay: 0, position: 'top-20 left-[15%]', label: 'Patient Health' },
    { Icon: Microscope, color: '#00C6FF', delay: 0.2, position: 'top-40 right-[20%]', label: 'Research' },
    { Icon: Pill, color: '#00ADB5', delay: 0.4, position: 'bottom-32 left-[25%]', label: 'Treatment' },
    { Icon: Activity, color: '#00C6FF', delay: 0.6, position: 'bottom-20 right-[15%]', label: 'Monitoring' },
  ];

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {/* 3D Floating Cubes */}
      {cubes.map(({ Icon, color, delay, position }, index) => (
        <motion.div
          key={index}
          className={`absolute ${position} hidden md:block`}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: delay + 0.5, duration: 0.8, type: 'spring' }}
          style={{
            perspective: '1000px',
            transformStyle: 'preserve-3d',
          }}
        >
          <motion.div
            className="relative"
            style={{
              rotateX: isMobile ? 0 : rotateX,
              rotateY: isMobile ? 0 : rotateY,
              transformStyle: 'preserve-3d',
            }}
            animate={{
              y: [0, -20, 0],
              rotateZ: [0, 5, -5, 0],
            }}
            transition={{
              duration: 4 + index,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            {/* 3D Cube */}
            <div className="relative w-20 h-20" style={{ transformStyle: 'preserve-3d' }}>
              {/* Front face */}
              <motion.div
                className="absolute inset-0 flex items-center justify-center rounded-lg backdrop-blur-sm border"
                style={{
                  backgroundColor: `${color}15`,
                  borderColor: `${color}30`,
                  transform: 'translateZ(40px)',
                }}
                animate={{
                  boxShadow: [
                    `0 0 20px ${color}30`,
                    `0 0 40px ${color}50`,
                    `0 0 20px ${color}30`,
                  ],
                }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Icon className="w-10 h-10" style={{ color }} />
              </motion.div>

              {/* Back face */}
              <div
                className="absolute inset-0 rounded-lg"
                style={{
                  backgroundColor: `${color}10`,
                  borderColor: `${color}20`,
                  transform: 'translateZ(-40px) rotateY(180deg)',
                  border: '1px solid',
                }}
              />

              {/* Top face */}
              <div
                className="absolute inset-0 rounded-lg"
                style={{
                  backgroundColor: `${color}12`,
                  borderColor: `${color}25`,
                  transform: 'rotateX(90deg) translateZ(40px)',
                  border: '1px solid',
                }}
              />

              {/* Bottom face */}
              <div
                className="absolute inset-0 rounded-lg"
                style={{
                  backgroundColor: `${color}08`,
                  borderColor: `${color}15`,
                  transform: 'rotateX(-90deg) translateZ(40px)',
                  border: '1px solid',
                }}
              />

              {/* Left face */}
              <div
                className="absolute inset-0 rounded-lg"
                style={{
                  backgroundColor: `${color}10`,
                  borderColor: `${color}20`,
                  transform: 'rotateY(-90deg) translateZ(40px)',
                  border: '1px solid',
                }}
              />

              {/* Right face */}
              <div
                className="absolute inset-0 rounded-lg"
                style={{
                  backgroundColor: `${color}10`,
                  borderColor: `${color}20`,
                  transform: 'rotateY(90deg) translateZ(40px)',
                  border: '1px solid',
                }}
              />
            </div>

            {/* Glow effect */}
            <motion.div
              className="absolute inset-0 rounded-lg blur-xl -z-10"
              style={{
                backgroundColor: color,
                opacity: 0.2,
              }}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.2, 0.4, 0.2],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
          </motion.div>
        </motion.div>
      ))}


    </div>
  );
}
