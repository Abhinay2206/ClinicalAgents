'use client';

import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import PageTransition from './PageTransition';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled 
          ? 'bg-[var(--bg-tertiary)]/90 backdrop-blur-2xl border-b border-[var(--border-subtle)] shadow-[0_8px_32px_rgba(0,0,0,0.08)]' 
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] flex items-center justify-center group-hover:scale-110 transition-transform">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-semibold text-[var(--text-primary)]">
              ClinicalAgent
            </span>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-6">
            <Link 
              href="#features" 
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-teal)] transition-colors"
            >
              Features
            </Link>
            <Link 
              href="#demo" 
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-teal)] transition-colors"
            >
              Demo
            </Link>
            <Link 
              href="#" 
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-teal)] transition-colors"
            >
              Docs
            </Link>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            {/* CTA Button with Transition */}
            <PageTransition href="/chat">
              <Button size="sm" className="hidden sm:inline-flex">
                Launch App
              </Button>
            </PageTransition>
          </div>
        </div>
      </div>
    </motion.nav>
  );
}
