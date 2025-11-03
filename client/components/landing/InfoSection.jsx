'use client';

import { motion, useScroll, useTransform, useInView } from 'framer-motion';
import { useRef } from 'react';
import { useIsMobile } from '@/hooks/useIsMobile';
import { 
  Brain, 
  Search, 
  BarChart3, 
  Shield, 
  Zap, 
  TrendingUp,
  FileText,
  Users,
  Clock,
  Target,
  Award,
  Sparkles
} from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Analysis',
    description: 'Advanced machine learning algorithms analyze clinical trial data with unprecedented accuracy and speed.',
    color: '#00ADB5',
  },
  {
    icon: Search,
    title: 'Smart Discovery',
    description: 'Intelligent search capabilities help you find relevant trials and insights instantly.',
    color: '#00C6FF',
  },
  {
    icon: BarChart3,
    title: 'Real-Time Analytics',
    description: 'Track trial progress, enrollment rates, and outcomes with comprehensive dashboards.',
    color: '#00ADB5',
  },
  {
    icon: Shield,
    title: 'Secure & Compliant',
    description: 'Enterprise-grade security ensuring HIPAA compliance and data protection.',
    color: '#00C6FF',
  },
];


const benefits = [
  {
    icon: Zap,
    title: 'Lightning Fast',
    description: 'Get insights in seconds, not hours',
  },
  {
    icon: Target,
    title: 'Precision Results',
    description: 'Highly accurate predictions and analysis',
  },
  {
    icon: TrendingUp,
    title: 'Continuous Learning',
    description: 'AI that improves with every interaction',
  },
  {
    icon: Sparkles,
    title: 'Intuitive Interface',
    description: 'Simple yet powerful user experience',
  },
];

// Feature card component with horizontal stack effect
function FeatureCard({ feature, index, isInView, scrollYProgress }) {
  const cardProgress = useTransform(
    scrollYProgress,
    [0.1 + index * 0.05, 0.3 + index * 0.05],
    [0, 1]
  );
  
  const x = useTransform(cardProgress, [0, 1], [index % 2 === 0 ? -200 : 200, 0]);
  const rotateY = useTransform(cardProgress, [0, 1], [index % 2 === 0 ? -25 : 25, 0]);
  const opacity = useTransform(cardProgress, [0, 0.5, 1], [0, 0.8, 1]);
  const scale = useTransform(cardProgress, [0, 1], [0.8, 1]);
  
  return (
    <motion.div
      style={{ 
        x,
        rotateY,
        opacity,
        scale,
        transformStyle: "preserve-3d"
      }}
      whileHover={{ 
        y: -8, 
        scale: 1.05,
        rotateY: 5,
        transition: { duration: 0.4, ease: "easeOut" } 
      }}
      className="relative group"
    >
      <div className="relative bg-[var(--bg-tertiary)] rounded-2xl p-8 border border-[var(--border-subtle)] shadow-[var(--shadow-soft)] hover:shadow-[var(--shadow-hover)] transition-all duration-300 h-full overflow-hidden">
        {/* Loading bar at bottom */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 h-1 rounded-b-2xl"
          style={{ backgroundColor: `${feature.color}30` }}
        >
          <motion.div
            className="h-full rounded-b-2xl"
            style={{ backgroundColor: feature.color }}
            initial={{ width: 0 }}
            animate={isInView ? { width: '100%' } : { width: 0 }}
            transition={{ duration: 1.2, delay: index * 0.15 + 0.4, ease: "easeInOut" }}
          />
        </motion.div>
        
        {/* Icon with loading animation */}
        <motion.div
          className="relative"
          initial={{ scale: 0, rotate: -90 }}
          animate={isInView ? { scale: 1, rotate: 0 } : { scale: 0, rotate: -90 }}
          transition={{ 
            duration: 0.8, 
            delay: index * 0.15 + 0.2,
            ease: [0.34, 1.56, 0.64, 1]
          }}
        >
          <feature.icon className="w-12 h-12 mb-6" style={{ color: feature.color }} />
        </motion.div>

        {/* Content with stagger animation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
        >
          <h3 className="text-xl font-semibold mb-3 text-[var(--text-primary)]">
            {feature.title}
          </h3>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            {feature.description}
          </p>
        </motion.div>

        {/* Corner accent */}
        <div
          className="absolute top-0 right-0 w-20 h-20 rounded-tr-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          style={{
            background: `linear-gradient(135deg, transparent 50%, ${feature.color}10 50%)`,
          }}
        />
      </div>
    </motion.div>
  );
}

export default function InfoSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });
  const isMobile = useIsMobile();
  
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"]
  });
  
  // Subtle parallax transforms for different layers (disabled on mobile)
  const headerY = useTransform(scrollYProgress, [0, 1], isMobile ? ['0px', '0px'] : ['0px', '-50px']);
  const contentY = useTransform(scrollYProgress, [0, 1], isMobile ? ['0px', '0px'] : ['0px', '-80px']);

  return (
    <section ref={ref} className="relative py-32 px-4 overflow-visible">
      {/* Background effects - removed as it will be on main container */}

      <div className="relative max-w-7xl mx-auto">
        {/* Section Header with subtle parallax */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          style={{ y: headerY }}
          className="text-center mb-20 will-change-transform"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={isInView ? { scale: 1 } : {}}
            transition={{ duration: 0.5, type: 'spring' }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] mb-6"
          >
            <Sparkles className="w-8 h-8 text-white" />
          </motion.div>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Why Choose{' '}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#00ADB5] to-[#00C6FF]">
              Clinical Agent
            </span>
          </h2>
          
          <p className="text-lg md:text-xl text-[var(--text-secondary)] max-w-3xl mx-auto">
            Revolutionizing clinical trial research with cutting-edge AI technology
          </p>
        </motion.div>

        {/* Features Grid with Horizontal Stack Effect and parallax */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.2 }}
          style={{ y: contentY, perspective: "2000px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-24 will-change-transform"
        >
          {features.map((feature, index) => (
            <FeatureCard 
              key={index}
              feature={feature}
              index={index}
              isInView={isInView}
              scrollYProgress={scrollYProgress}
            />
          ))}
        </motion.div>

        {/* Benefits Grid */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {benefits.map((benefit, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30, scale: 0.95 }}
              animate={isInView ? { opacity: 1, x: 0, scale: 1 } : { opacity: 0, x: index % 2 === 0 ? -30 : 30, scale: 0.95 }}
              transition={{ 
                duration: 1.0, 
                delay: index * 0.15,
                ease: [0.25, 0.46, 0.45, 0.94]
              }}
              whileHover={{ 
                scale: 1.03,
                transition: { duration: 0.4, ease: "easeOut" } 
              }}
              className="flex items-start gap-4 p-6 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] hover:border-[#00ADB5]/30 transition-all duration-300 relative overflow-hidden group"
            >
              {/* Pulse loading effect */}
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-[#00ADB5]/5 to-[#00C6FF]/5"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={isInView ? { 
                  opacity: [0, 0.5, 0],
                  scale: [0.8, 1.2, 0.8]
                } : {}}
                transition={{ 
                  duration: 2,
                  delay: 0.7 + index * 0.1,
                  repeat: 0
                }}
              />

              <div className="flex-shrink-0 relative">
                <motion.div 
                  className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] flex items-center justify-center"
                  initial={{ rotate: -180, scale: 0 }}
                  animate={isInView ? { rotate: 0, scale: 1 } : {}}
                  transition={{ 
                    duration: 0.5, 
                    delay: 0.8 + index * 0.1,
                    type: 'spring'
                  }}
                  whileHover={{ rotate: 360 }}
                >
                  <benefit.icon className="w-5 h-5 text-white" />
                </motion.div>
                
                {/* Spinning ring loader */}
                <motion.div
                  className="absolute inset-0 rounded-lg border-2 border-[#00ADB5] border-t-transparent"
                  initial={{ rotate: 0, opacity: 1 }}
                  animate={isInView ? { 
                    rotate: 360,
                    opacity: 0
                  } : {}}
                  transition={{ 
                    duration: 0.8,
                    delay: 0.8 + index * 0.1,
                    ease: 'easeOut'
                  }}
                />
              </div>
              
              <motion.div
                initial={{ opacity: 0 }}
                animate={isInView ? { opacity: 1 } : {}}
                transition={{ duration: 0.4, delay: 0.9 + index * 0.1 }}
              >
                <h4 className="font-semibold mb-1 text-[var(--text-primary)]">
                  {benefit.title}
                </h4>
                <p className="text-sm text-[var(--text-secondary)]">
                  {benefit.description}
                </p>
              </motion.div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
