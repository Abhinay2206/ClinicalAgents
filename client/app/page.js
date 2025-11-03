'use client';

import { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import IntroAnimation from '@/components/landing/IntroAnimation';
import CustomCursor from '@/components/landing/CustomCursor';
import FloatingParticles from '@/components/landing/FloatingParticles';
import MorphingBackground from '@/components/landing/MorphingBackground';
import Navbar from '@/components/landing/Navbar';
import HeroSection from '@/components/landing/HeroSection';
import FeaturesSection from '@/components/landing/FeaturesSection';
import DemoSection from '@/components/landing/DemoSection';
import CTASection from '@/components/landing/CTASection';
import NewsletterSection from '@/components/landing/NewsletterSection';
import Footer from '@/components/landing/Footer';

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
      {/* Custom Cursor */}
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
          <FeaturesSection />
          <DemoSection />
          <CTASection />
          <NewsletterSection />
          <Footer />
        </>
      )}
    </main>
  );
}
