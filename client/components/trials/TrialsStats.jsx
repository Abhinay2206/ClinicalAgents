'use client';

import { motion } from 'framer-motion';
import { BarChart3, Activity, FlaskConical, FileCheck } from 'lucide-react';
import { Card } from '@/components/ui/card';

export default function TrialsStats({ trials, filteredTrials }) {
    // Calculate statistics
    const totalTrials = filteredTrials.length;
    const allTrials = trials.length;

    // Status breakdown
    const statusCounts = filteredTrials.reduce((acc, trial) => {
        const status = trial['Overall Status'] || 'Unknown';
        acc[status] = (acc[status] || 0) + 1;
        return acc;
    }, {});

    // Phase breakdown
    const phaseCounts = filteredTrials.reduce((acc, trial) => {
        const phase = trial.Phase || 'N/A';
        acc[phase] = (acc[phase] || 0) + 1;
        return acc;
    }, {});

    // Get top statuses
    const topStatuses = Object.entries(statusCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 4);

    const statCards = [
        {
            icon: FileCheck,
            label: 'Total Trials',
            value: totalTrials,
            total: allTrials,
            color: 'text-[var(--accent-teal)]',
            bgColor: 'bg-[var(--accent-teal)]/10'
        },
        {
            icon: Activity,
            label: 'Recruiting',
            value: statusCounts['RECRUITING'] || 0,
            color: 'text-green-500',
            bgColor: 'bg-green-500/10'
        },
        {
            icon: BarChart3,
            label: 'Active',
            value: statusCounts['ACTIVE'] || statusCounts['ACTIVE, NOT RECRUITING'] || 0,
            color: 'text-blue-500',
            bgColor: 'bg-blue-500/10'
        },
        {
            icon: FlaskConical,
            label: 'Completed',
            value: statusCounts['COMPLETED'] || 0,
            color: 'text-amber-500',
            bgColor: 'bg-amber-500/10'
        }
    ];

    return (
        <div className="space-y-4 mb-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {statCards.map((stat, index) => (
                    <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: index * 0.1 }}
                    >
                        <Card className="p-4 hover:border-[var(--accent-teal)]/30 transition-all">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <p className="text-xs text-[var(--text-tertiary)] mb-2">
                                        {stat.label}
                                    </p>
                                    <div className="flex items-baseline gap-2">
                                        <motion.p
                                            className={`text-2xl font-bold ${stat.color}`}
                                            initial={{ scale: 0.5 }}
                                            animate={{ scale: 1 }}
                                            transition={{
                                                type: 'spring',
                                                stiffness: 200,
                                                delay: index * 0.1 + 0.2
                                            }}
                                        >
                                            {stat.value.toLocaleString()}
                                        </motion.p>
                                        {stat.total && (
                                            <span className="text-xs text-[var(--text-tertiary)]">
                                                / {stat.total}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                                    <stat.icon className={`w-4 h-4 ${stat.color}`} />
                                </div>
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </div>

            {/* Phase Distribution */}
            {Object.keys(phaseCounts).length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.4 }}
                >
                    <Card className="p-4">
                        <h4 className="text-sm font-semibold text-[var(--text-secondary)] mb-3">
                            Phase Distribution
                        </h4>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(phaseCounts)
                                .sort(([, a], [, b]) => b - a)
                                .map(([phase, count]) => (
                                    <div
                                        key={phase}
                                        className="px-3 py-1.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] flex items-center gap-2"
                                    >
                                        <span className="text-xs font-medium text-[var(--text-primary)]">
                                            {phase === 'NA' ? 'N/A' : phase.replace('PHASE', 'Phase ')}
                                        </span>
                                        <span className="text-xs font-bold text-[var(--accent-teal)]">
                                            {count}
                                        </span>
                                    </div>
                                ))}
                        </div>
                    </Card>
                </motion.div>
            )}
        </div>
    );
}
