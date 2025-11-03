'use client';

import { useState, useEffect, lazy, Suspense } from 'react';
import { AnimatePresence } from 'framer-motion';
import IntroAnimation from '@/components/landing/IntroAnimation';
import CustomCursor from '@/components/landing/CustomCursor';
import FloatingParticles from '@/components/landing/FloatingParticles';
import MorphingBackground from '@/components/landing/MorphingBackground';
import Navbar from '@/components/landing/Navbar';
import HeroSection from '@/components/landing/HeroSection';

// Lazy load components that are below the fold
const FeaturesSection = lazy(() => import('@/components/landing/FeaturesSection'));
const DemoSection = lazy(() => import('@/components/landing/DemoSection'));
const CTASection = lazy(() => import('@/components/landing/CTASection'));
const NewsletterSection = lazy(() => import('@/components/landing/NewsletterSection'));
const Footer = lazy(() => import('@/components/landing/Footer'));

export default function LandingPage() {
  const [showIntro, setShowIntro] = useState(true);
  const [hasSeenIntro, setHasSeenIntro] = useState(false);

  useEffect(() => {
    // Check if user has seen intro before
    const seen = sessionStorage.getItem('hasSeenIntro');
    if (seen === 'true') {
      setShowIntro(false);
      setHasSeenIntro(true);
    }
  }, []);

  const handleIntroComplete = () => {
    sessionStorage.setItem('hasSeenIntro', 'true');
    setShowIntro(false);
    setHasSeenIntro(true);
  };

  return (
    <main className="min-h-screen">
      {/* Custom Cursor - Only on desktop */}
      <CustomCursor />
      
      {/* Morphing Background */}
      <MorphingBackground />
      
      {/* Floating Particles Background */}
      <FloatingParticles />
      
      <AnimatePresence mode="wait">
        {showIntro && !hasSeenIntro && (
          <IntroAnimation key="intro" onComplete={handleIntroComplete} />
        )}
      </AnimatePresence>

      {/* Landing Page Content */}
      {(hasSeenIntro || !showIntro) && (
        <>
          <Navbar />
          <HeroSection />
          <Suspense fallback={<div className="h-screen" />}>
            <FeaturesSection />
            <DemoSection />
            <CTASection />
            <NewsletterSection />
            <Footer />
          </Suspense>
        </>
      )}
    </main>
  );
}
