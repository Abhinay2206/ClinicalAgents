'use client';

import { motion, useInView, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';
import { useIsMobile } from '@/hooks/useIsMobile';
import { Search, Brain, BarChart3, CheckCircle2, ArrowRight } from 'lucide-react';

const steps = [
  {
    icon: Search,
    title: 'Query Your Data',
    description: 'Ask questions in natural language about clinical trials, efficacy, safety, and enrollment criteria.',
    detail: 'Our intelligent chatbot understands complex medical terminology and research context.',
    color: '#00ADB5',
  },
  {
    icon: Brain,
    title: 'AI Analysis',
    description: 'Advanced AI models process your query against our comprehensive clinical trial database.',
    detail: 'Machine learning algorithms identify patterns, correlations, and insights from vast datasets.',
    color: '#00C6FF',
  },
  {
    icon: BarChart3,
    title: 'Get Insights',
    description: 'Receive detailed, evidence-based answers with relevant data visualizations and references.',
    detail: 'Interactive dashboards and charts make complex data easy to understand.',
    color: '#00ADB5',
  },
  {
    icon: CheckCircle2,
    title: 'Make Decisions',
    description: 'Use the insights to make informed decisions about trial design, patient selection, and strategy.',
    detail: 'Export reports and share findings with your research team.',
    color: '#00C6FF',
  },
];

// Individual step component to use hooks properly
function StepItem({ step, index, isInView }) {
  const stepRef = useRef(null);
  const stepInView = useInView(stepRef, { 
    once: false, 
    amount: 0.3,
    margin: "-50px 0px -50px 0px"
  });

  return (
    <motion.div
      ref={stepRef}
      initial={{ opacity: 0, x: index % 2 === 0 ? -80 : 80, scale: 0.9 }}
      animate={stepInView ? { 
        opacity: 1, 
        x: 0,
        scale: 1
      } : { 
        opacity: 0, 
        x: index % 2 === 0 ? -80 : 80,
        scale: 0.9
      }}
      transition={{ 
        duration: 1.2,
        ease: [0.25, 0.46, 0.45, 0.94],
        opacity: { duration: 1.0 },
        scale: { duration: 1.2 }
      }}
      className={`flex flex-col lg:flex-row items-center gap-12 ${
        index % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'
      }`}
    >
      {/* Content */}
      <div className={`flex-1 ${index % 2 === 0 ? 'lg:text-right' : 'lg:text-left'}`}>
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="bg-[var(--bg-tertiary)] rounded-3xl p-8 md:p-10 border border-[var(--border-subtle)] shadow-[var(--shadow-soft)] hover:shadow-[var(--shadow-hover)] transition-all duration-300 relative overflow-hidden group"
        >
          {/* Loading shimmer sweep */}
          <motion.div
            className="absolute inset-0 opacity-0 group-hover:opacity-100"
            initial={{ x: '-100%' }}
            whileHover={{
              x: '100%',
              transition: {
                duration: 1.2,
                ease: 'easeInOut',
              },
            }}
            style={{
              background: `linear-gradient(90deg, transparent, ${step.color}20, transparent)`,
              width: '50%',
            }}
          />

          {/* Corner accent */}
          <div
            className="absolute top-0 right-0 w-32 h-32 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
            style={{
              background: `radial-gradient(circle at top right, ${step.color}15, transparent)`,
            }}
          />

          {/* Step number with loading animation */}
          <motion.div
            className="inline-flex items-center justify-center w-12 h-12 rounded-xl font-bold text-xl mb-6 relative"
            style={{
              backgroundColor: `${step.color}15`,
              color: step.color,
            }}
            initial={{ scale: 0, rotate: -90 }}
            animate={stepInView ? { scale: 1, rotate: 0 } : { scale: 0, rotate: -90 }}
            transition={{ 
              duration: 0.8, 
              delay: 0.2,
              ease: [0.34, 1.56, 0.64, 1]
            }}
          >
            {index + 1}
            
            {/* Circular loading ring */}
            <motion.div
              className="absolute inset-0 rounded-xl border-2"
              style={{ borderColor: step.color, borderTopColor: 'transparent' }}
              initial={{ rotate: 0, opacity: 1 }}
              animate={stepInView ? { 
                rotate: 360,
                opacity: 0
              } : { rotate: 0, opacity: 1 }}
              transition={{ 
                duration: 1.2,
                delay: 0.2,
                ease: "easeOut"
              }}
            />
          </motion.div>

          {/* Content with staggered loading */}
          <motion.h3 
            className="text-2xl md:text-3xl font-bold mb-4 text-[var(--text-primary)]"
            initial={{ opacity: 0, y: 15 }}
            animate={stepInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 15 }}
            transition={{ duration: 0.9, delay: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            {step.title}
          </motion.h3>
          
          <motion.p 
            className="text-lg text-[var(--text-secondary)] mb-4 leading-relaxed"
            initial={{ opacity: 0, y: 15 }}
            animate={stepInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 15 }}
            transition={{ duration: 0.9, delay: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            {step.description}
          </motion.p>
          
          <motion.p 
            className="text-[var(--text-tertiary)] leading-relaxed"
            initial={{ opacity: 0, y: 15 }}
            animate={stepInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 15 }}
            transition={{ duration: 0.9, delay: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            {step.detail}
          </motion.p>

          {/* Animated underline with loading effect */}
          <motion.div
            className="h-1 rounded-full mt-6 relative"
            style={{ backgroundColor: `${step.color}30` }}
          >
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{ backgroundColor: step.color }}
              initial={{ width: 0 }}
              animate={stepInView ? { width: '60px' } : { width: 0 }}
              transition={{ duration: 1.2, delay: 0.9, ease: "easeInOut" }}
            />
          </motion.div>
        </motion.div>
      </div>

      {/* Icon */}
      <motion.div
        className="flex-shrink-0 relative"
        initial={{ scale: 0, rotate: -90, opacity: 0 }}
        animate={stepInView ? { scale: 1, rotate: 0, opacity: 1 } : { scale: 0, rotate: -90, opacity: 0 }}
        transition={{ 
          duration: 1.0, 
          delay: 0.1,
          ease: [0.34, 1.56, 0.64, 1]
        }}
        whileHover={{ scale: 1.05, rotate: 5, transition: { duration: 0.3 } }}
      >
        <div
          className="w-32 h-32 rounded-3xl flex items-center justify-center relative"
          style={{
            backgroundColor: `${step.color}15`,
          }}
        >
          {/* Single rotating ring with loading effect */}
          <motion.div
            className="absolute inset-0 rounded-3xl border-2"
            style={{ borderColor: `${step.color}30` }}
            initial={{ rotate: 0, scale: 1.3, opacity: 0 }}
            animate={stepInView ? { 
              rotate: 180,
              scale: 1,
              opacity: 1
            } : { rotate: 0, scale: 1.3, opacity: 0 }}
            transition={{ 
              duration: 1.4,
              delay: 0.1,
              ease: "easeOut"
            }}
          />
          
          {/* Loading spinner during initial load */}
          <motion.div
            className="absolute inset-0 rounded-3xl border-2 border-t-transparent"
            style={{ borderColor: step.color }}
            initial={{ rotate: 0, opacity: 1 }}
            animate={stepInView ? { 
              rotate: 360,
              opacity: 0
            } : { rotate: 0, opacity: 1 }}
            transition={{ 
              duration: 1.5,
              delay: 0.1,
              ease: "easeInOut"
            }}
          />

          {/* Icon with pop-in effect */}
          <motion.div
            initial={{ scale: 0, rotate: -45 }}
            animate={stepInView ? { scale: 1, rotate: 0 } : { scale: 0, rotate: -45 }}
            transition={{ 
              duration: 0.8, 
              delay: 0.4,
              ease: [0.34, 1.56, 0.64, 1]
            }}
          >
            <step.icon className="w-16 h-16 relative z-10" style={{ color: step.color }} />
          </motion.div>

          {/* Glow effect */}
          <motion.div
            className="absolute inset-0 rounded-3xl blur-2xl -z-10"
            style={{ backgroundColor: step.color }}
            animate={{
              opacity: [0.2, 0.4, 0.2],
              scale: [1, 1.1, 1],
            }}
            transition={{ duration: 3, repeat: Infinity }}
          />
        </div>
      </motion.div>

      {/* Spacer for non-icon side */}
      <div className="flex-1 hidden lg:block" />
    </motion.div>
  );
}

export default function HowItWorksSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: false, amount: 0.1 });
  const isMobile = useIsMobile();
  
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"]
  });
  
  // Layered parallax effects (disabled on mobile for performance)
  const headerY = useTransform(scrollYProgress, [0, 1], isMobile ? ['0px', '0px'] : ['0px', '-40px']);
  const contentY = useTransform(scrollYProgress, [0, 1], isMobile ? ['0px', '0px'] : ['0px', '-60px']);
  const gridY = useTransform(scrollYProgress, [0, 1], isMobile ? ['0px', '0px'] : ['0px', '40px']);

  return (
    <section ref={ref} className="relative py-32 px-4 overflow-hidden">
      {/* Background removed - using unified background from parent */}
      
      {/* Grid pattern with parallax */}
      <motion.div 
        className="absolute inset-0 opacity-[0.03] will-change-transform" 
        style={{ 
          y: gridY,
          backgroundImage: 'linear-gradient(#00ADB5 1px, transparent 1px), linear-gradient(90deg, #00ADB5 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }} 
      />

      <div className="relative max-w-7xl mx-auto">
        {/* Section Header with parallax */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          style={{ y: headerY }}
          className="text-center mb-24 will-change-transform"
        >
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={isInView ? { scale: 1, rotate: 0 } : {}}
            transition={{ duration: 0.6, type: 'spring', stiffness: 200 }}
            className="inline-block mb-6"
          >
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] flex items-center justify-center relative">
              <motion.div
                className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] blur-xl opacity-50"
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.5, 0.8, 0.5],
                }}
                transition={{ duration: 3, repeat: Infinity }}
              />
              <ArrowRight className="w-10 h-10 text-white relative z-10" />
            </div>
          </motion.div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            How It{' '}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#00ADB5] to-[#00C6FF]">
              Works
            </span>
          </h2>
          
          <p className="text-lg md:text-xl text-[var(--text-secondary)] max-w-3xl mx-auto">
            Transform your clinical trial research workflow in four simple steps
          </p>
        </motion.div>

        {/* Steps with parallax */}
        <motion.div className="relative will-change-transform" style={{ y: contentY }}>
          {/* Connection Line */}
          <motion.div
            className="absolute top-24 left-1/2 -translate-x-1/2 w-1 bg-gradient-to-b from-[#00ADB5] via-[#00C6FF] to-[#00ADB5] hidden lg:block"
            style={{ height: 'calc(100% - 200px)' }}
            initial={{ scaleY: 0 }}
            animate={isInView ? { scaleY: 1 } : {}}
            transition={{ duration: 1.5, delay: 0.5 }}
          />

          <div className="space-y-32 lg:space-y-40">
            {steps.map((step, index) => (
              <StepItem key={index} step={step} index={index} isInView={isInView} />
            ))}
          </div>
        </motion.div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 1 }}
          className="text-center mt-24"
        >
          <motion.a
            href="/chat"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-[#00ADB5] to-[#00C6FF] text-white rounded-2xl font-semibold text-lg shadow-lg hover:shadow-2xl transition-all duration-300"
          >
            Try It Now
            <motion.span
              animate={{ x: [0, 5, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              →
            </motion.span>
          </motion.a>
        </motion.div>
      </div>
    </section>
  );
}
