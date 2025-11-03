'use client';

import { lazy, Suspense, useState, useEffect } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import CustomCursor from '@/components/landing/CustomCursor';
import EnhancedParticles from '@/components/landing/EnhancedParticles';
import FloatingIcons from '@/components/landing/FloatingIcons';
import RippleEffect from '@/components/landing/RippleEffect';
import AnimatedGradientOverlay from '@/components/landing/AnimatedGradientOverlay';
import ParallaxBackground from '@/components/landing/ParallaxBackground';
import ScrollProgress from '@/components/landing/ScrollProgress';
import SmoothScrollProvider from '@/components/landing/SmoothScrollProvider';
import Navbar from '@/components/landing/Navbar';
import HeroSection from '@/components/landing/HeroSection';
import InfoSection from '@/components/landing/InfoSection';
import HowItWorksSection from '@/components/landing/HowItWorksSection';

// Lazy load components that are below the fold
const FeaturesSection = lazy(() => import('@/components/landing/FeaturesSection'));
const DemoSection = lazy(() => import('@/components/landing/DemoSection'));
const CTASection = lazy(() => import('@/components/landing/CTASection'));
const NewsletterSection = lazy(() => import('@/components/landing/NewsletterSection'));
const Footer = lazy(() => import('@/components/landing/Footer'));

function LandingPageContent() {
  const [isMobile, setIsMobile] = useState(false);
  const { scrollYProgress } = useScroll();
  
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  // Parallax transforms for background layers (disabled on mobile)
  const bgY1 = useTransform(scrollYProgress, [0, 1], isMobile ? ['0%', '0%'] : ['0%', '15%']);
  const bgY2 = useTransform(scrollYProgress, [0, 1], isMobile ? ['0%', '0%'] : ['0%', '25%']);
  const bgY3 = useTransform(scrollYProgress, [0, 1], isMobile ? ['0%', '0%'] : ['0%', '20%']);
  
  // Particle and icon parallax (disabled on mobile)
  const particleY = useTransform(scrollYProgress, [0, 1], isMobile ? ['0%', '0%'] : ['0%', '30%']);
  const iconY = useTransform(scrollYProgress, [0, 1], isMobile ? ['0%', '0%'] : ['0%', '40%']);

  return (
    <main className="min-h-screen relative overflow-x-hidden">
      {/* Scroll Progress Bar */}
      <ScrollProgress />
        
        {/* Custom Cursor - Only on desktop */}
        <CustomCursor />
        
        {/* Click Ripple Effect */}
        <RippleEffect />
        
        {/* Animated Gradient Overlay */}
        <AnimatedGradientOverlay />
        
        {/* Multi-layered Parallax Background */}
        <motion.div style={{ y: bgY1 }} className="will-change-transform">
          <ParallaxBackground />
        </motion.div>
        
        {/* Enhanced Particles Background with Lines - Subtle parallax */}
        <motion.div style={{ y: particleY }} className="will-change-transform">
          <EnhancedParticles />
        </motion.div>
        
        {/* Floating Icons for added depth - More parallax */}
        <motion.div style={{ y: iconY }} className="will-change-transform">
          <FloatingIcons />
        </motion.div>
        
        {/* Main content wrapper with consistent background (all sections except footer) */}
        <div className="relative">
          {/* Unified Background - Dark gradient base */}
          <div className="absolute inset-0 bg-gradient-to-b from-[var(--bg-secondary)] via-[var(--bg-primary)] to-[var(--bg-secondary)]" />
          
          {/* Grid pattern background with parallax - matching HowItWorks style */}
          <motion.div 
            style={{ 
              y: bgY1,
              backgroundImage: 'linear-gradient(#00ADB5 1px, transparent 1px), linear-gradient(90deg, #00ADB5 1px, transparent 1px)',
              backgroundSize: '60px 60px',
            }}
            className="absolute inset-0 opacity-[0.03] will-change-transform pointer-events-none"
          />
          
          {/* Animated gradient blobs with parallax */}
          <motion.div 
            style={{ y: bgY2 }}
            className="absolute top-20 left-[10%] w-96 h-96 rounded-full bg-gradient-to-br from-[#00ADB5]/10 to-transparent blur-3xl will-change-transform"
          >
            <div className="w-full h-full rounded-full bg-gradient-to-br from-[#00ADB5]/10 to-transparent blur-3xl animate-pulse" style={{ animationDuration: '8s' }} />
          </motion.div>
          <motion.div 
            style={{ y: bgY3 }}
            className="absolute top-[40%] right-[5%] w-[500px] h-[500px] rounded-full will-change-transform"
          >
            <div className="w-full h-full rounded-full bg-gradient-to-tl from-[#00C6FF]/10 to-transparent blur-3xl animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }} />
          </motion.div>
          <motion.div 
            style={{ y: bgY1 }}
            className="absolute bottom-20 left-[15%] w-80 h-80 rounded-full will-change-transform"
          >
            <div className="w-full h-full rounded-full bg-gradient-to-tr from-[#00ADB5]/10 to-transparent blur-3xl animate-pulse" style={{ animationDuration: '12s', animationDelay: '4s' }} />
          </motion.div>
        
          {/* Landing Page Content */}
          <div className="relative z-10">
            <Navbar />
            <HeroSection />
            
            {/* Info Section - Right after hero with clear information */}
            <InfoSection />
            
            {/* How It Works Section - Step by step explanation */}
            <HowItWorksSection />
            
            {/* Lazy loaded sections with same unified background */}
            <Suspense fallback={<div className="h-screen flex items-center justify-center">
              <div className="w-8 h-8 border-2 border-[var(--accent-teal)] border-t-transparent rounded-full animate-spin" />
            </div>}>
              <FeaturesSection />
              <DemoSection />
              <CTASection />
              <NewsletterSection />
            </Suspense>
          </div>
        </div>
        
        {/* Footer outside the background wrapper */}
        <Footer />
    </main>
  );
}

export default function LandingPage() {
  return (
    <SmoothScrollProvider>
      <LandingPageContent />
    </SmoothScrollProvider>
  );
}
