'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowLeft, Loader2, AlertCircle, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { chatService } from '@/services/chatService';

export default function TrialsPage() {
    const [disease, setDisease] = useState('');
    const [trials, setTrials] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searched, setSearched] = useState(false);
    const [expandedTrials, setExpandedTrials] = useState(new Set());

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!disease.trim()) return;

        setLoading(true);
        setError(null);
        setTrials([]);
        setSearched(true);

        try {
            const result = await chatService.searchTrials(disease);
            setTrials(result.trials || []);
        } catch (err) {
            setError(err.message || 'Failed to search trials');
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        if (!status) return 'bg-gray-500';
        const statusUpper = status.toUpperCase();
        if (statusUpper.includes('ACTIVE') || statusUpper.includes('RECRUITING')) return 'bg-green-500';
        if (statusUpper.includes('ENROLLING')) return 'bg-yellow-500';
        if (statusUpper.includes('COMPLETED')) return 'bg-blue-500';
        if (statusUpper.includes('TERMINATED') || statusUpper.includes('SUSPENDED')) return 'bg-red-500';
        if (statusUpper.includes('WITHDRAWN')) return 'bg-gray-500';
        return 'bg-gray-400';
    };

    const toggleExpanded = (nctId) => {
        const newExpanded = new Set(expandedTrials);
        if (newExpanded.has(nctId)) {
            newExpanded.delete(nctId);
        } else {
            newExpanded.add(nctId);
        }
        setExpandedTrials(newExpanded);
    };

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] overflow-hidden relative">
            {/* Background effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-20 left-[10%] w-96 h-96 rounded-full bg-gradient-to-br from-[#00ADB5]/10 to-transparent blur-3xl animate-pulse" style={{ animationDuration: '8s' }} />
                <div className="absolute top-[40%] right-[5%] w-[500px] h-[500px] rounded-full bg-gradient-to-tl from-[#00C6FF]/10 to-transparent blur-3xl animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }} />
                <div className="absolute bottom-20 left-[20%] w-80 h-80 rounded-full bg-gradient-to-tr from-[#00ADB5]/5 to-transparent blur-3xl" />
            </div>

            <div className="relative z-10 max-w-7xl mx-auto px-4 py-12">
                {/* Back Button */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                    className="mb-8"
                >
                    <Link href="/predict">
                        <Button variant="ghost" className="gap-2 hover:bg-white/5">
                            <ArrowLeft className="w-4 h-4" />
                            Back to Prediction
                        </Button>
                    </Link>
                </motion.div>

                {/* Page Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-12"
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#00ADB5]/10 border border-[#00ADB5]/20 mb-6 backdrop-blur-sm"
                    >
                        <FileText className="w-5 h-5 text-[#00ADB5]" />
                        <span className="text-sm font-medium text-[#00ADB5]">Clinical Trials Database</span>
                    </motion.div>

                    <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 tracking-tight">
                        Browse <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#00ADB5] to-[#00C6FF]">Clinical Trials</span>
                    </h1>

                    <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto">
                        Search for clinical trials by disease name to find available studies
                    </p>
                </motion.div>

                {/* Search Form */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="max-w-2xl mx-auto mb-12"
                >
                    <Card className="p-2 bg-[var(--bg-tertiary)]/50 backdrop-blur-xl border-[var(--border-subtle)]">
                        <form onSubmit={handleSearch} className="flex gap-2">
                            <input
                                type="text"
                                value={disease}
                                onChange={(e) => setDisease(e.target.value)}
                                placeholder="Enter disease name (e.g., diabetes, cancer)"
                                className="flex-1 px-6 py-4 rounded-xl bg-transparent text-lg text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none"
                                autoFocus
                            />
                            <Button
                                type="submit"
                                disabled={loading || !disease.trim()}
                                size="lg"
                                className="rounded-xl px-8"
                            >
                                {loading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Search className="w-5 h-5" />
                                )}
                            </Button>
                        </form>
                    </Card>
                </motion.div>

                {/* Results */}
                <div className="max-w-5xl mx-auto min-h-[400px]">
                    <AnimatePresence mode="wait">
                        {loading && (
                            <motion.div
                                key="loading"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="flex flex-col items-center justify-center py-20"
                            >
                                <div className="relative">
                                    <div className="absolute inset-0 blur-xl bg-[#00ADB5]/20 rounded-full" />
                                    <Loader2 className="w-12 h-12 text-[#00ADB5] animate-spin relative z-10" />
                                </div>
                                <p className="text-[var(--text-secondary)] mt-4 font-medium">Searching clinical trials database...</p>
                            </motion.div>
                        )}

                        {error && (
                            <motion.div
                                key="error"
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                className="flex flex-col items-center justify-center py-20"
                            >
                                <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-8 max-w-md text-center backdrop-blur-sm">
                                    <AlertCircle className="w-12 h-12 text-red-500 mb-4 mx-auto" />
                                    <p className="text-red-500 font-semibold text-lg mb-2">Search Failed</p>
                                    <p className="text-sm text-[var(--text-secondary)]">{error}</p>
                                </div>
                            </motion.div>
                        )}

                        {!loading && !error && searched && trials.length === 0 && (
                            <motion.div
                                key="no-results"
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                className="flex flex-col items-center justify-center py-20"
                            >
                                <div className="bg-[var(--bg-tertiary)]/50 border border-[var(--border-subtle)] rounded-2xl p-10 max-w-md text-center backdrop-blur-sm">
                                    <FileText className="w-16 h-16 text-[var(--text-tertiary)] mb-4 mx-auto opacity-50" />
                                    <p className="font-semibold text-xl mb-2">No Trials Found</p>
                                    <p className="text-[var(--text-secondary)]">
                                        No clinical trials found for "{disease}". Try a different search term.
                                    </p>
                                </div>
                            </motion.div>
                        )}

                        {!loading && !error && trials.length > 0 && (
                            <motion.div
                                key="results"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="space-y-4"
                            >
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="mb-6 text-center"
                                >
                                    <p className="text-[var(--text-secondary)]">
                                        Found <span className="font-semibold text-[var(--text-primary)]">{trials.length}</span> clinical trial{trials.length !== 1 ? 's' : ''} for "{disease}"
                                    </p>
                                </motion.div>

                                {trials.map((trial, index) => {
                                    const isExpanded = expandedTrials.has(trial['NCT ID']);

                                    return (
                                        <motion.div
                                            key={trial['NCT ID'] || index}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ duration: 0.4, delay: index * 0.05 }}
                                        >
                                            <Card className="p-6 hover:border-[#00ADB5]/30 group">
                                                <div className="flex items-start justify-between gap-4">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-3 mb-3 flex-wrap">
                                                            <h3 className="text-lg font-bold text-[#00ADB5] group-hover:text-[#00C6FF] transition-colors">
                                                                {trial['NCT ID'] || 'N/A'}
                                                            </h3>
                                                            {trial['Overall Status'] && (
                                                                <span className={`px-3 py-1 rounded-full text-xs font-bold text-white shadow-sm ${getStatusColor(trial['Overall Status'])}`}>
                                                                    {trial['Overall Status']}
                                                                </span>
                                                            )}
                                                            {trial.Phase && (
                                                                <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                                                    {trial.Phase}
                                                                </span>
                                                            )}
                                                        </div>

                                                        {trial.Conditions && (
                                                            <p className="text-[var(--text-primary)] font-medium mb-2 text-lg">
                                                                {trial.Conditions}
                                                            </p>
                                                        )}

                                                        {trial['Study Type'] && (
                                                            <p className="text-sm text-[var(--text-secondary)] mb-2">
                                                                <span className="font-medium text-[var(--text-tertiary)]">Study Type:</span> {trial['Study Type']}
                                                            </p>
                                                        )}

                                                        <AnimatePresence>
                                                            {isExpanded && (
                                                                <motion.div
                                                                    initial={{ opacity: 0, height: 0 }}
                                                                    animate={{ opacity: 1, height: 'auto' }}
                                                                    exit={{ opacity: 0, height: 0 }}
                                                                    className="overflow-hidden"
                                                                >
                                                                    <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] space-y-4">
                                                                        {trial['Eligibility Criteria'] && (
                                                                            <div>
                                                                                <p className="text-sm font-semibold mb-2 text-[var(--accent-teal)]">Eligibility Criteria</p>
                                                                                <div className="text-sm text-[var(--text-secondary)] whitespace-pre-wrap bg-[var(--bg-primary)]/50 p-4 rounded-lg border border-[var(--border-subtle)]">
                                                                                    {trial['Eligibility Criteria'].substring(0, 500)}
                                                                                    {trial['Eligibility Criteria'].length > 500 && '...'}
                                                                                </div>
                                                                            </div>
                                                                        )}

                                                                        {trial['Why Stopped'] && trial['Why Stopped'] !== 'nan' && (
                                                                            <div>
                                                                                <p className="text-sm font-semibold mb-1 text-red-400">Why Stopped</p>
                                                                                <p className="text-sm text-[var(--text-secondary)]">
                                                                                    {trial['Why Stopped']}
                                                                                </p>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </motion.div>
                                                            )}
                                                        </AnimatePresence>
                                                    </div>

                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => toggleExpanded(trial['NCT ID'])}
                                                        className="flex-shrink-0 rounded-full hover:bg-[var(--accent-teal)]/10 hover:text-[var(--accent-teal)]"
                                                    >
                                                        <motion.div
                                                            animate={{ rotate: isExpanded ? 180 : 0 }}
                                                            transition={{ duration: 0.3 }}
                                                        >
                                                            <ChevronDown className="w-5 h-5" />
                                                        </motion.div>
                                                    </Button>
                                                </div>
                                            </Card>
                                        </motion.div>
                                    );
                                })}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
