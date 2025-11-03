'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, CheckCircle } from 'lucide-react';

export default function NewsletterSection() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, success, error

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    
    // Simulate API call
    setTimeout(() => {
      setStatus('success');
      setEmail('');
      setTimeout(() => setStatus('idle'), 3000);
    }, 1500);
  };

  return (
    <section className="relative py-20 px-4 bg-[var(--bg-secondary)] overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-[#00ADB5] rounded-full blur-3xl"></div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="relative max-w-4xl mx-auto text-center"
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] mb-6"
        >
          <span className="w-2 h-2 rounded-full bg-[#00ADB5] animate-pulse"></span>
          <span className="text-sm font-medium text-[var(--accent-teal)]">Stay Updated</span>
        </motion.div>

        {/* Heading */}
        <h2 className="text-3xl md:text-5xl font-bold text-[var(--text-primary)] mb-4">
          Get the latest insights
        </h2>
        <p className="text-lg text-[var(--text-secondary)] mb-8 max-w-2xl mx-auto">
          Subscribe to our newsletter for updates on clinical research, AI innovations, and product releases.
        </p>

        {/* Email Form */}
        <motion.form
          onSubmit={handleSubmit}
          className="max-w-md mx-auto"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="relative flex items-center gap-2">
            <div className="relative flex-1">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                disabled={status === 'loading' || status === 'success'}
                className="w-full px-6 py-4 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-teal)] focus:border-transparent transition-all disabled:opacity-50"
              />
            </div>
            
            <motion.button
              type="submit"
              disabled={status === 'loading' || status === 'success'}
              whileHover={{ scale: status === 'idle' ? 1.05 : 1 }}
              whileTap={{ scale: status === 'idle' ? 0.95 : 1 }}
              className="px-6 py-4 rounded-xl bg-gradient-to-r from-[#00ADB5] to-[#00C6FF] text-white font-medium flex items-center gap-2 shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === 'success' ? (
                <>
                  <CheckCircle className="w-5 h-5" />
                  <span className="hidden sm:inline">Subscribed!</span>
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  <span className="hidden sm:inline">
                    {status === 'loading' ? 'Sending...' : 'Subscribe'}
                  </span>
                </>
              )}
            </motion.button>
          </div>

          <p className="mt-4 text-xs text-[var(--text-tertiary)]">
            We respect your privacy. Unsubscribe at any time.
          </p>
        </motion.form>

        {/* Success Message */}
        {status === 'success' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 text-[var(--accent-teal)] text-sm font-medium"
          >
            ✨ Thanks for subscribing! Check your inbox for confirmation.
          </motion.div>
        )}
      </motion.div>
    </section>
  );
}
