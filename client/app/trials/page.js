'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowLeft, Loader2, AlertCircle, FileText, ChevronDown, ExternalLink, Copy, Check, SlidersHorizontal } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { chatService } from '@/services/chatService';
import FilterPanel from '@/components/trials/FilterPanel';
import TrialsStats from '@/components/trials/TrialsStats';

export default function TrialsPage() {
    const [disease, setDisease] = useState('');
    const [trials, setTrials] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searched, setSearched] = useState(false);
    const [expandedTrials, setExpandedTrials] = useState(new Set());
    const [copiedId, setCopiedId] = useState(null);
    const [showMobileFilters, setShowMobileFilters] = useState(false);

    // Filter state
    const [filters, setFilters] = useState({
        statuses: [],
        phases: [],
        studyType: ''
    });

    // Sort state
    const [sortBy, setSortBy] = useState('status'); // status, phase, conditions

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!disease.trim()) return;

        setLoading(true);
        setError(null);
        setTrials([]);
        setSearched(true);
        setFilters({ statuses: [], phases: [], studyType: '' }); // Reset filters on new search

        try {
            const result = await chatService.searchTrials(disease);
            setTrials(result.trials || []);
        } catch (err) {
            setError(err.message || 'Failed to search trials');
        } finally {
            setLoading(false);
        }
    };

    // Apply filters and sorting
    const filteredAndSortedTrials = useMemo(() => {
        let filtered = [...trials];

        // Apply status filter
        if (filters.statuses.length > 0) {
            filtered = filtered.filter(trial => {
                const status = (trial['Overall Status'] || '').toUpperCase().replace(/ /g, '_');
                return filters.statuses.some(s => status.includes(s));
            });
        }

        // Apply phase filter
        if (filters.phases.length > 0) {
            filtered = filtered.filter(trial => {
                const phase = (trial.Phase || 'NA').toUpperCase().replace(/ /g, '');
                return filters.phases.includes(phase);
            });
        }

        // Apply study type filter
        if (filters.studyType) {
            filtered = filtered.filter(trial => {
                const type = (trial['Study Type'] || '').toUpperCase().replace(/ /g, '_');
                return type.includes(filters.studyType);
            });
        }

        // Apply sorting
        filtered.sort((a, b) => {
            if (sortBy === 'status') {
                return (a['Overall Status'] || '').localeCompare(b['Overall Status'] || '');
            } else if (sortBy === 'phase') {
                return (a.Phase || '').localeCompare(b.Phase || '');
            } else if (sortBy === 'conditions') {
                return (a.Conditions || '').localeCompare(b.Conditions || '');
            }
            return 0;
        });

        return filtered;
    }, [trials, filters, sortBy]);

    // Count active filters
    const activeFilterCount = filters.statuses.length + filters.phases.length + (filters.studyType ? 1 : 0);

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

    const handleCopyNctId = async (nctId) => {
        try {
            await navigator.clipboard.writeText(nctId);
            setCopiedId(nctId);
            setTimeout(() => setCopiedId(null), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const clearFilters = () => {
        setFilters({ statuses: [], phases: [], studyType: '' });
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
                        Search and filter clinical trials with advanced options
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

                {/* Results Section - Two Column Layout */}
                {searched && !loading && !error && trials.length > 0 && (
                    <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6">
                        {/* Filters Sidebar - Desktop */}
                        <div className="hidden lg:block">
                            <FilterPanel
                                filters={filters}
                                onFilterChange={setFilters}
                                onClearFilters={clearFilters}
                                activeCount={activeFilterCount}
                            />
                        </div>

                        {/* Main Content */}
                        <div>
                            {/* Mobile Filter Button */}
                            <div className="lg:hidden mb-4">
                                <Button
                                    variant="outline"
                                    onClick={() => setShowMobileFilters(true)}
                                    className="w-full gap-2"
                                >
                                    <SlidersHorizontal className="w-4 h-4" />
                                    Filters
                                    {activeFilterCount > 0 && (
                                        <span className="ml-auto px-2 py-0.5 rounded-full bg-[var(--accent-teal)]/20 text-[var(--accent-teal)] text-xs font-bold">
                                            {activeFilterCount}
                                        </span>
                                    )}
                                </Button>
                            </div>

                            {/* Statistics Dashboard */}
                            <TrialsStats trials={trials} filteredTrials={filteredAndSortedTrials} />

                            {/* Sort Controls */}
                            <div className="flex items-center justify-between mb-6">
                                <p className="text-sm text-[var(--text-secondary)]">
                                    Showing <span className="font-semibold text-[var(--text-primary)]">{filteredAndSortedTrials.length}</span> of {trials.length} trials
                                </p>
                                <select
                                    value={sortBy}
                                    onChange={(e) => setSortBy(e.target.value)}
                                    className="px-4 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-teal)]"
                                >
                                    <option value="status">Sort by Status</option>
                                    <option value="phase">Sort by Phase</option>
                                    <option value="conditions">Sort by Condition</option>
                                </select>
                            </div>

                            {/* Trials List */}
                            <AnimatePresence mode="wait">
                                {filteredAndSortedTrials.length === 0 ? (
                                    <motion.div
                                        key="no-filtered-results"
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                        className="flex flex-col items-center justify-center py-20"
                                    >
                                        <div className="bg-[var(--bg-tertiary)]/50 border border-[var(--border-subtle)] rounded-2xl p-10 max-w-md text-center backdrop-blur-sm">
                                            <FileText className="w-16 h-16 text-[var(--text-tertiary)] mb-4 mx-auto opacity-50" />
                                            <p className="font-semibold text-xl mb-2">No Matching Trials</p>
                                            <p className="text-[var(--text-secondary)] mb-4">
                                                No trials match your current filters
                                            </p>
                                            <Button variant="outline" onClick={clearFilters}>
                                                Clear Filters
                                            </Button>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="results"
                                        className="space-y-4"
                                    >
                                        {filteredAndSortedTrials.map((trial, index) => {
                                            const isExpanded = expandedTrials.has(trial['NCT ID']);
                                            const nctUrl = `https://clinicaltrials.gov/study/${trial['NCT ID']}`;

                                            return (
                                                <motion.div
                                                    key={trial['NCT ID'] || index}
                                                    initial={{ opacity: 0, y: 20 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    transition={{ duration: 0.4, delay: Math.min(index * 0.05, 0.5) }}
                                                >
                                                    <Card className="p-6 hover:border-[#00ADB5]/30 group">
                                                        <div className="flex items-start justify-between gap-4">
                                                            <div className="flex-1">
                                                                {/* Header */}
                                                                <div className="flex items-center gap-3 mb-3 flex-wrap">
                                                                    <div className="flex items-center gap-2">
                                                                        <h3 className="text-lg font-bold text-[#00ADB5] group-hover:text-[#00C6FF] transition-colors">
                                                                            {trial['NCT ID'] || 'N/A'}
                                                                        </h3>
                                                                        <button
                                                                            onClick={() => handleCopyNctId(trial['NCT ID'])}
                                                                            className="p-1 hover:bg-[var(--bg-secondary)] rounded transition-colors"
                                                                            title="Copy NCT ID"
                                                                        >
                                                                            {copiedId === trial['NCT ID'] ? (
                                                                                <Check className="w-3.5 h-3.5 text-green-500" />
                                                                            ) : (
                                                                                <Copy className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                                                                            )}
                                                                        </button>
                                                                        <a
                                                                            href={nctUrl}
                                                                            target="_blank"
                                                                            rel="noopener noreferrer"
                                                                            className="p-1 hover:bg-[var(--bg-secondary)] rounded transition-colors"
                                                                            title="View on ClinicalTrials.gov"
                                                                        >
                                                                            <ExternalLink className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                                                                        </a>
                                                                    </div>
                                                                    {trial['Overall Status'] && (
                                                                        <span className={`px-3 py-1 rounded-full text-xs font-bold text-white shadow-sm ${getStatusColor(trial['Overall Status'])}`}>
                                                                            {trial['Overall Status']}
                                                                        </span>
                                                                    )}
                                                                    {trial.Phase && (
                                                                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#00ADB5]/10 text-[#00ADB5] border border-[#00ADB5]/20">
                                                                            {trial.Phase}
                                                                        </span>
                                                                    )}
                                                                </div>

                                                                {/* Conditions */}
                                                                {trial.Conditions && (
                                                                    <p className="text-[var(--text-primary)] font-medium mb-2 text-lg">
                                                                        {trial.Conditions}
                                                                    </p>
                                                                )}

                                                                {/* Study Type */}
                                                                {trial['Study Type'] && (
                                                                    <p className="text-sm text-[var(--text-secondary)] mb-2">
                                                                        <span className="font-medium text-[var(--text-tertiary)]">Study Type:</span> {trial['Study Type']}
                                                                    </p>
                                                                )}

                                                                {/* Expanded Content */}
                                                                <AnimatePresence>
                                                                    {isExpanded && (
                                                                        <motion.div
                                                                            initial={{ opacity: 0, height: 0 }}
                                                                            animate={{ opacity: 1, height: 'auto' }}
                                                                            exit={{ opacity: 0, height: 0 }}
                                                                            className="overflow-hidden"
                                                                        >
                                                                            <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] space-y-4">
                                                                                {/* Eligibility Criteria */}
                                                                                {trial['Eligibility Criteria'] && trial['Eligibility Criteria'] !== 'nan' && (
                                                                                    <div>
                                                                                        <p className="text-sm font-semibold mb-2 text-[var(--accent-teal)]">Eligibility Criteria</p>
                                                                                        <div className="text-sm text-[var(--text-secondary)] whitespace-pre-wrap bg-[var(--bg-primary)]/50 p-4 rounded-lg border border-[var(--border-subtle)] max-h-60 overflow-y-auto">
                                                                                            {trial['Eligibility Criteria']}
                                                                                        </div>
                                                                                    </div>
                                                                                )}

                                                                                {/* Why Stopped */}
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

                                                            {/* Expand Button */}
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
                )}

                {/* Loading State */}
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

                    {/* Error State */}
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

                    {/* No Results */}
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
                </AnimatePresence>
            </div>

            {/* Mobile Filter Drawer */}
            <AnimatePresence>
                {showMobileFilters && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setShowMobileFilters(false)}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
                        />

                        {/* Drawer */}
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed left-0 top-0 bottom-0 w-80 bg-[var(--bg-primary)] z-50 overflow-y-auto lg:hidden"
                        >
                            <div className="p-6">
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className="text-lg font-semibold">Filters</h3>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setShowMobileFilters(false)}
                                    >
                                        <X className="w-5 h-5" />
                                    </Button>
                                </div>
                                <FilterPanel
                                    filters={filters}
                                    onFilterChange={setFilters}
                                    onClearFilters={clearFilters}
                                    activeCount={activeFilterCount}
                                />
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}
