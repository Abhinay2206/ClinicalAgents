'use client';

import { motion, useScroll, useTransform } from 'framer-motion';
import { Users, BarChart3, ShieldCheck, Search } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { useRef } from 'react';

const features = [
  {
    icon: Users,
    title: "Patient Enrollment",
    description: "Identify optimal participants efficiently with AI-powered matching algorithms.",
    gradient: "from-emerald-500 to-teal-500",
    color: "#10b981"
  },
  {
    icon: BarChart3,
    title: "Efficacy Analysis",
    description: "Compare outcomes across studies with comprehensive data visualization.",
    gradient: "from-blue-500 to-cyan-500",
    color: "#3b82f6"
  },
  {
    icon: ShieldCheck,
    title: "Safety Monitoring",
    description: "Detect adverse trends early with real-time monitoring and alerts.",
    gradient: "from-red-500 to-pink-500",
    color: "#ef4444"
  },
  {
    icon: Search,
    title: "Trial Search",
    description: "Query global registries instantly with natural language processing.",
    gradient: "from-purple-500 to-indigo-500",
    color: "#8b5cf6"
  }
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.1
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 60, scale: 0.9 },
  show: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 15
    }
  }
};

export default function FeaturesSection() {
  const sectionRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start']
  });

  const y = useTransform(scrollYProgress, [0, 1], [100, -100]);
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  return (
    <section 
      id="features" 
      ref={sectionRef}
      className="relative py-32 px-4 bg-[var(--bg-primary)] scroll-mt-20 overflow-hidden"
    >
      {/* Parallax decorative elements */}
      <motion.div 
        className="absolute top-20 right-10 w-64 h-64 rounded-full bg-[#00ADB5]/5 blur-3xl pointer-events-none"
        style={{ y, opacity }}
      />
      <motion.div 
        className="absolute bottom-20 left-10 w-80 h-80 rounded-full bg-[#00C6FF]/5 blur-3xl pointer-events-none"
        style={{ y: useTransform(scrollYProgress, [0, 1], [-100, 100]), opacity }}
      />
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Section Header with Badge */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-20"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            whileInView={{ opacity: 1, scale: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-[#00ADB5]/10 to-[#00C6FF]/10 border border-[#00ADB5]/20 mb-8 backdrop-blur-sm"
          >
            <motion.span 
              className="w-2 h-2 rounded-full bg-[#00ADB5]"
              animate={{ 
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1]
              }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <span className="text-sm font-medium text-[var(--accent-teal)] tracking-wide">AI POWERED</span>
          </motion.div>
          
          <motion.h2 
            className="text-4xl md:text-6xl font-bold text-[var(--text-primary)] mb-6"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.3 }}
          >
            Intelligent Features
          </motion.h2>
          
          <motion.p 
            className="text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            Powerful tools for clinical research excellence
          </motion.p>
        </motion.div>

        {/* Feature Cards with 3D perspective */}
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-150px" }}
          className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto"
          style={{ perspective: "1000px" }}
        >
          {features.map((feature, index) => (
            <motion.div 
              key={index} 
              variants={item}
              whileHover={{ 
                y: -12,
                rotateX: 5,
                scale: 1.02,
                transition: { type: "spring", stiffness: 300, damping: 20 }
              }}
              className="transform-gpu"
            >
              <Card className="h-full group cursor-pointer overflow-hidden relative border-[var(--border-subtle)] hover:border-[#00ADB5]/40 transition-all duration-500 backdrop-blur-sm bg-[var(--bg-tertiary)]/80">
                {/* Animated gradient on hover */}
                <motion.div 
                  className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-[0.05] transition-opacity duration-700`}
                  initial={false}
                />
                
                {/* Glow effect */}
                <motion.div
                  className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                  style={{
                    background: `radial-gradient(circle at 50% 50%, ${feature.color}10 0%, transparent 70%)`
                  }}
                />
                
                <CardHeader className="space-y-4 relative z-10">
                  <motion.div 
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center shadow-lg`}
                    whileHover={{ 
                      rotate: [0, -10, 10, -10, 0],
                      scale: 1.1
                    }}
                    transition={{ duration: 0.5 }}
                  >
                    <feature.icon className="w-5 h-5 text-white" />
                  </motion.div>
                  <CardTitle className="text-lg font-semibold">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
