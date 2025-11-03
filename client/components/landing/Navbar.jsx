'use client';

import { useState, useEffect } from 'react';
import { Sparkles, Moon, Sun } from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import PageTransition from './PageTransition';

export default function Navbar() {
  const [isDark, setIsDark] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }

    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleDarkMode = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', !isDark ? 'dark' : 'light');
  };

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled 
          ? 'bg-[var(--bg-tertiary)]/80 backdrop-blur-xl border-b border-[var(--border-subtle)] shadow-[var(--shadow-soft)]' 
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
            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg hover:bg-[var(--bg-secondary)] transition-all"
              title="Toggle Theme"
            >
              {isDark ? (
                <Sun className="w-5 h-5 text-[var(--accent-teal)]" />
              ) : (
                <Moon className="w-5 h-5 text-[var(--text-secondary)]" />
              )}
            </button>

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
