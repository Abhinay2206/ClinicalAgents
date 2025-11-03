'use client';

import { Sparkles, Github, Twitter, Linkedin, Mail } from 'lucide-react';
import Link from 'next/link';
import { motion } from 'framer-motion';

const footerSections = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '#features' },
      { label: 'Demo', href: '#demo' },
      { label: 'Pricing', href: '#' },
      { label: 'Roadmap', href: '#' },
    ]
  },
  {
    title: 'Resources',
    links: [
      { label: 'Documentation', href: '#' },
      { label: 'API Reference', href: '#' },
      { label: 'Guides', href: '#' },
      { label: 'Support', href: '#' },
    ]
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '#' },
      { label: 'Blog', href: '#' },
      { label: 'Careers', href: '#' },
      { label: 'Contact', href: '#' },
    ]
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy Policy', href: '#' },
      { label: 'Terms of Service', href: '#' },
      { label: 'Cookie Policy', href: '#' },
      { label: 'HIPAA Compliance', href: '#' },
    ]
  }
];

const socialLinks = [
  { icon: Twitter, href: '#', label: 'Twitter' },
  { icon: Github, href: '#', label: 'GitHub' },
  { icon: Linkedin, href: '#', label: 'LinkedIn' },
  { icon: Mail, href: '#', label: 'Email' },
];

export default function Footer() {
  return (
    <footer className="relative bg-[var(--bg-primary)] overflow-hidden">
      {/* Gradient Line */}
      <div className="h-px bg-gradient-to-r from-transparent via-[#00ADB5] to-transparent" />
      
      {/* Background Decoration */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#00ADB5] rounded-full blur-3xl"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 py-16">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-12 mb-12">
          {/* Brand Section */}
          <div className="lg:col-span-2">
            <motion.div 
              className="flex items-center gap-3 mb-4"
              whileHover={{ scale: 1.02 }}
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00ADB5] to-[#00C6FF] flex items-center justify-center shadow-lg">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-[var(--text-primary)]">
                ClinicalAgent
              </span>
            </motion.div>
            <p className="text-sm text-[var(--text-secondary)] mb-6 leading-relaxed">
              Accelerating clinical research with AI-powered intelligence. 
              Built for researchers, by researchers.
            </p>
            
            {/* Social Links */}
            <div className="flex items-center gap-3">
              {socialLinks.map((social, index) => (
                <motion.a
                  key={index}
                  href={social.href}
                  whileHover={{ scale: 1.1, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="w-9 h-9 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--accent-teal)] hover:text-white text-[var(--text-secondary)] flex items-center justify-center transition-all"
                  aria-label={social.label}
                >
                  <social.icon className="w-4 h-4" />
                </motion.a>
              ))}
            </div>
          </div>

          {/* Links Sections */}
          {footerSections.map((section, index) => (
            <div key={index}>
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4 uppercase tracking-wider">
                {section.title}
              </h3>
              <ul className="space-y-3">
                {section.links.map((link, linkIndex) => (
                  <li key={linkIndex}>
                    <Link
                      href={link.href}
                      className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-teal)] transition-colors inline-block hover:translate-x-1 transition-transform"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-[var(--border-subtle)]">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-[var(--text-tertiary)] text-center md:text-left">
              © 2025 ClinicalAgent. All rights reserved. Built with ❤️ for clinical research.
            </p>
            <div className="flex items-center gap-6 text-xs text-[var(--text-tertiary)]">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                All systems operational
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
