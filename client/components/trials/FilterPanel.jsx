'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Filter, X, ChevronDown } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function FilterPanel({ filters, onFilterChange, onClearFilters, activeCount }) {
    const [isOpen, setIsOpen] = useState(true);

    const statusOptions = [
        'RECRUITING',
        'ACTIVE',
        'COMPLETED',
        'TERMINATED',
        'SUSPENDED',
        'WITHDRAWN',
        'ENROLLING',
        'NOT_YET_RECRUITING'
    ];

    const phaseOptions = [
        'PHASE1',
        'PHASE2',
        'PHASE3',
        'PHASE4',
        'NA'
    ];

    const handleStatusToggle = (status) => {
        const newStatuses = filters.statuses.includes(status)
            ? filters.statuses.filter(s => s !== status)
            : [...filters.statuses, status];
        onFilterChange({ ...filters, statuses: newStatuses });
    };

    const handlePhaseToggle = (phase) => {
        const newPhases = filters.phases.includes(phase)
            ? filters.phases.filter(p => p !== phase)
            : [...filters.phases, phase];
        onFilterChange({ ...filters, phases: newPhases });
    };

    const handleStudyTypeChange = (type) => {
        onFilterChange({ ...filters, studyType: type === filters.studyType ? '' : type });
    };

    const formatLabel = (text) => {
        return text
            .replace(/_/g, ' ')
            .toLowerCase()
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    const formatPhase = (phase) => {
        if (phase === 'NA') return 'N/A';
        return phase.replace('PHASE', 'Phase ');
    };

    return (
        <Card className="p-6 bg-[var(--bg-tertiary)]/50 backdrop-blur-xl border-[var(--border-subtle)] sticky top-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-[var(--accent-teal)]" />
                    <h3 className="text-lg font-semibold text-[var(--text-primary)]">Filters</h3>
                    {activeCount > 0 && (
                        <motion.span
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="px-2 py-0.5 rounded-full bg-[var(--accent-teal)]/20 text-[var(--accent-teal)] text-xs font-bold"
                        >
                            {activeCount}
                        </motion.span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {activeCount > 0 && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onClearFilters}
                            className="text-xs text-[var(--text-tertiary)] hover:text-[var(--accent-teal)]"
                        >
                            Clear All
                        </Button>
                    )}
                    <button
                        onClick={() => setIsOpen(!isOpen)}
                        className="lg:hidden p-1 hover:bg-[var(--bg-secondary)] rounded transition-colors"
                    >
                        <motion.div
                            animate={{ rotate: isOpen ? 180 : 0 }}
                            transition={{ duration: 0.2 }}
                        >
                            <ChevronDown className="w-4 h-4" />
                        </motion.div>
                    </button>
                </div>
            </div>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="space-y-6 overflow-hidden"
                    >
                        {/* Status Filter */}
                        <div>
                            <h4 className="text-sm font-semibold text-[var(--text-secondary)] mb-3">
                                Trial Status
                            </h4>
                            <div className="space-y-2">
                                {statusOptions.map((status) => (
                                    <label
                                        key={status}
                                        className="flex items-center gap-2 cursor-pointer group"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={filters.statuses.includes(status)}
                                            onChange={() => handleStatusToggle(status)}
                                            className="w-4 h-4 rounded border-[var(--border-subtle)] bg-[var(--bg-secondary)] text-[var(--accent-teal)] focus:ring-2 focus:ring-[var(--accent-teal)]/20 transition-all cursor-pointer"
                                        />
                                        <span className="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                                            {formatLabel(status)}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Phase Filter */}
                        <div className="pt-4 border-t border-[var(--border-subtle)]">
                            <h4 className="text-sm font-semibold text-[var(--text-secondary)] mb-3">
                                Trial Phase
                            </h4>
                            <div className="space-y-2">
                                {phaseOptions.map((phase) => (
                                    <label
                                        key={phase}
                                        className="flex items-center gap-2 cursor-pointer group"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={filters.phases.includes(phase)}
                                            onChange={() => handlePhaseToggle(phase)}
                                            className="w-4 h-4 rounded border-[var(--border-subtle)] bg-[var(--bg-secondary)] text-[var(--accent-teal)] focus:ring-2 focus:ring-[var(--accent-teal)]/20 transition-all cursor-pointer"
                                        />
                                        <span className="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                                            {formatPhase(phase)}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Study Type Filter */}
                        <div className="pt-4 border-t border-[var(--border-subtle)]">
                            <h4 className="text-sm font-semibold text-[var(--text-secondary)] mb-3">
                                Study Type
                            </h4>
                            <div className="space-y-2">
                                {['INTERVENTIONAL', 'OBSERVATIONAL', 'EXPANDED_ACCESS'].map((type) => (
                                    <label
                                        key={type}
                                        className="flex items-center gap-2 cursor-pointer group"
                                    >
                                        <input
                                            type="radio"
                                            name="studyType"
                                            checked={filters.studyType === type}
                                            onChange={() => handleStudyTypeChange(type)}
                                            className="w-4 h-4 border-[var(--border-subtle)] bg-[var(--bg-secondary)] text-[var(--accent-teal)] focus:ring-2 focus:ring-[var(--accent-teal)]/20 transition-all cursor-pointer"
                                        />
                                        <span className="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                                            {formatLabel(type)}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </Card>
    );
}
