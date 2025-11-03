'use client';

import { motion, useScroll, useTransform } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import { useRef } from 'react';

export default function CTASection() {
  const sectionRef = useRef(null);
  
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start']
  });

  const y = useTransform(scrollYProgress, [0, 1], [100, -100]);
  const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.8, 1, 0.9]);
  const opacity = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [0, 1, 1, 0]);

  return (
    <section 
      ref={sectionRef}
      className="relative py-32 px-4 bg-[var(--bg-primary)] overflow-hidden"
    >
      {/* Parallax background orbs */}
      <motion.div 
        className="absolute top-0 left-1/4 w-96 h-96 rounded-full bg-[#00ADB5]/5 blur-3xl pointer-events-none"
        style={{ y, opacity }}
      />
      <motion.div 
        className="absolute bottom-0 right-1/4 w-80 h-80 rounded-full bg-[#00C6FF]/5 blur-3xl pointer-events-none"
        style={{ y: useTransform(scrollYProgress, [0, 1], [-100, 100]), opacity }}
      />

      <motion.div
        initial={{ opacity: 0, y: 60 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        style={{ scale }}
        className="max-w-5xl mx-auto relative z-10"
      >
        <div className="relative rounded-3xl overflow-hidden"
          style={{ transformStyle: "preserve-3d" }}
        >
          {/* Gradient Background */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#00ADB5] via-[#00C6FF] to-[#00ADB5] bg-[length:200%_100%]">
            <motion.div
              animate={{
                backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
              }}
              transition={{
                duration: 8,
                repeat: Infinity,
                ease: "linear"
              }}
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
            />
          </div>

          {/* Glow Effect */}
          <motion.div
            className="absolute inset-0"
            animate={{
              boxShadow: [
                "0 0 60px rgba(0, 173, 181, 0.4)",
                "0 0 80px rgba(0, 198, 255, 0.6)",
                "0 0 60px rgba(0, 173, 181, 0.4)"
              ]
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />

          {/* Content */}
          <div className="relative z-10 px-8 py-16 md:px-16 md:py-24 text-center">
            {/* Decorative Elements */}
            <div className="absolute top-10 left-10 w-20 h-20 rounded-full bg-white/10 blur-2xl"></div>
            <div className="absolute bottom-10 right-10 w-32 h-32 rounded-full bg-white/10 blur-3xl"></div>
            
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm border border-white/30 mb-8"
            >
              <span className="w-2 h-2 rounded-full bg-white animate-pulse"></span>
              <span className="text-sm font-medium text-white">Ready to Transform Your Research?</span>
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight"
            >
              Empower your research<br />with AI-driven insights
            </motion.h2>
            
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="text-lg md:text-xl text-white/90 mb-10 max-w-2xl mx-auto font-light"
            >
              Join leading researchers accelerating clinical trials with intelligent automation
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            >
              <motion.a 
                href="/chat"
                whileHover={{ scale: 1.05 }} 
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  size="lg"
                  className="bg-white text-[#00ADB5] hover:bg-white/90 shadow-2xl text-base px-8 py-6 gap-2 group"
                >
                  Get Started Free
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </motion.a>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  size="lg"
                  variant="ghost"
                  className="text-white border-2 border-white/30 hover:bg-white/10 backdrop-blur-sm px-8 py-6"
                >
                  Watch Demo
                </Button>
              </motion.div>
            </motion.div>

            {/* Trust Indicators */}
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="mt-12 flex items-center justify-center gap-8 text-white/70 text-sm"
            >
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span>Trusted by researchers</span>
              </div>
              <div className="hidden sm:block w-px h-4 bg-white/30"></div>
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>HIPAA Compliant</span>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
