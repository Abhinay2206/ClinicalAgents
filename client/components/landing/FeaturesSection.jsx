'use client';

import { motion } from 'framer-motion';
import { Users, BarChart3, ShieldCheck, Search } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

const features = [
  {
    icon: Users,
    title: "Patient Enrollment",
    description: "Identify optimal participants efficiently with AI-powered matching algorithms.",
    gradient: "from-emerald-500 to-teal-500"
  },
  {
    icon: BarChart3,
    title: "Efficacy Analysis",
    description: "Compare outcomes across studies with comprehensive data visualization.",
    gradient: "from-blue-500 to-cyan-500"
  },
  {
    icon: ShieldCheck,
    title: "Safety Monitoring",
    description: "Detect adverse trends early with real-time monitoring and alerts.",
    gradient: "from-red-500 to-pink-500"
  },
  {
    icon: Search,
    title: "Trial Search",
    description: "Query global registries instantly with natural language processing.",
    gradient: "from-purple-500 to-indigo-500"
  }
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

export default function FeaturesSection() {
  return (
    <section id="features" className="py-24 px-4 bg-[var(--bg-primary)] scroll-mt-20">
      <div className="max-w-7xl mx-auto">
        {/* Section Header with Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#00ADB5]/5 border border-[#00ADB5]/10 mb-8"
          >
            <span className="text-xs font-medium text-[var(--accent-teal)] tracking-wide">AI POWERED</span>
          </motion.div>
          <h2 className="text-4xl md:text-5xl font-bold text-[var(--text-primary)] mb-4">
            Features
          </h2>
          <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto">
            Intelligent tools for clinical research
          </p>
        </motion.div>

        {/* Feature Cards */}
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto"
        >
          {features.map((feature, index) => (
            <motion.div 
              key={index} 
              variants={item}
              whileHover={{ y: -8 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
            >
              <Card className="h-full group cursor-pointer overflow-hidden relative border-[var(--border-subtle)] hover:border-[#00ADB5]/30 transition-all">
                {/* Subtle gradient on hover */}
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-[0.03] transition-opacity duration-500`} />
                
                <CardHeader className="space-y-3">
                  <motion.div 
                    className={`w-10 h-10 rounded-lg bg-gradient-to-br ${feature.gradient} flex items-center justify-center`}
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.6 }}
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
