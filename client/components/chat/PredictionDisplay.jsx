'use client';

import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
    CheckCircleIcon,
    XCircleIcon,
    ChartBarIcon,
    UserGroupIcon,
    ShieldCheckIcon,
    BeakerIcon
} from '@heroicons/react/24/outline';

export default function PredictionDisplay({ content }) {
    // Parse the prediction response
    const parseResponse = (text) => {
        const result = {
            prediction: 'UNKNOWN',
            confidence: 0,
            reasoning: '',
            stepByStep: '',
            enrollment: '',
            safety: '',
            efficacy: ''
        };

        // Extract prediction
        const predMatch = text.match(/\*\*Prediction\*\*:\s*(PASS|FAIL)/i) ||
            text.match(/🎯 Prediction:\s*(PASS|FAIL)/i);
        if (predMatch) result.prediction = predMatch[1].toUpperCase();

        // Extract confidence
        const confMatch = text.match(/\*\*Confidence\*\*:\s*(\d+)%/i) ||
            text.match(/📊 Confidence:\s*(\d+)%/i);
        if (confMatch) result.confidence = parseInt(confMatch[1]);

        // Extract reasoning section
        const reasoningMatch = text.match(/## 💭 Reasoning\s+([\s\S]*?)(?=\n##|\n\*\*|Agent Reports:|$)/i);
        if (reasoningMatch) result.reasoning = reasoningMatch[1].trim();

        // Extract step-by-step analysis
        const stepsMatch = text.match(/## 📊 Step-by-Step Analysis\s+([\s\S]*?)(?=\n## 💭|Agent Reports:|$)/i);
        if (stepsMatch) result.stepByStep = stepsMatch[1].trim();

        // Extract agent reports
        const enrollmentMatch = text.match(/Enrollment:\s*([\s\S]*?)(?=Safety:|Efficacy:|$)/i);
        if (enrollmentMatch) result.enrollment = enrollmentMatch[1].trim();

        const safetyMatch = text.match(/Safety:\s*([\s\S]*?)(?=Efficacy:|$)/i);
        if (safetyMatch) result.safety = safetyMatch[1].trim();

        const efficacyMatch = text.match(/Efficacy:\s*([\s\S]*?)$/i);
        if (efficacyMatch) result.efficacy = efficacyMatch[1].trim();

        return result;
    };

    const data = parseResponse(content);
    const isPassed = data.prediction === 'PASS';

    return (
        <div className="space-y-4 w-full">
            {/* Main Prediction Card */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`
          rounded-2xl border-2 p-6
          ${isPassed
                        ? 'bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border-emerald-500/30'
                        : 'bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/30'
                    }
        `}
            >
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        {isPassed ? (
                            <CheckCircleIcon className="w-10 h-10 text-emerald-500" />
                        ) : (
                            <XCircleIcon className="w-10 h-10 text-red-500" />
                        )}
                        <div>
                            <h3 className="text-2xl font-bold text-[var(--text-primary)]">
                                {data.prediction}
                            </h3>
                            <p className="text-sm text-[var(--text-secondary)]">Clinical Trial Prediction</p>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="flex items-center gap-2">
                            <ChartBarIcon className="w-5 h-5 text-[var(--text-secondary)]" />
                            <span className="text-3xl font-bold text-[var(--text-primary)]">
                                {data.confidence}%
                            </span>
                        </div>
                        <p className="text-xs text-[var(--text-tertiary)] mt-1">Confidence</p>
                    </div>
                </div>

                {/* Reasoning */}
                {data.reasoning && (
                    <div className="mt-4 p-4 rounded-xl bg-[var(--bg-secondary)]/50 border border-[var(--border-subtle)]">
                        <h4 className="text-sm font-semibold text-[var(--text-secondary)] mb-2 flex items-center gap-2">
                            <span>💭</span> Key Reasoning
                        </h4>
                        <div className="text-sm text-[var(--text-primary)] leading-relaxed prose prose-sm max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.reasoning}</ReactMarkdown>
                        </div>
                    </div>
                )}
            </motion.div>

            {/* Step-by-Step Analysis - Collapsible */}
            {data.stepByStep && (
                <motion.details
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="group rounded-xl bg-[var(--bg-tertiary)]/50 border border-[var(--border-subtle)] overflow-hidden"
                >
                    <summary className="cursor-pointer p-4 hover:bg-[var(--bg-secondary)]/30 transition-colors list-none">
                        <div className="flex items-center justify-between">
                            <h4 className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
                                <span>📊</span> Detailed Step-by-Step Analysis
                            </h4>
                            <svg className="w-5 h-5 text-[var(--text-secondary)] transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </div>
                    </summary>
                    <div className="p-4 pt-0">
                        {/* Parse and render individual steps */}
                        {data.stepByStep.split(/### Step \d+:/).filter(Boolean).map((step, idx) => {
                            const stepIcons = ['👥', '🛡️', '⚗️', '⚖️'];
                            const stepColors = ['text-blue-500', 'text-amber-500', 'text-purple-500', 'text-emerald-500'];
                            return (
                                <div key={idx} className="mb-4 last:mb-0">
                                    <div className="flex items-start gap-3">
                                        <div className={`flex-shrink-0 w-8 h-8 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-subtle)] flex items-center justify-center ${stepColors[idx % 4]}`}>
                                            <span className="text-lg">{stepIcons[idx % 4]}</span>
                                        </div>
                                        <div className="flex-1">
                                            <h5 className="font-semibold text-[var(--text-primary)] mb-2">
                                                Step {idx + 1}: {step.split('\n')[0].trim()}
                                            </h5>
                                            <div className="text-sm text-[var(--text-secondary)] leading-relaxed prose prose-sm max-w-none">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {step.split('\n').slice(1).join('\n').trim()}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </motion.details>
            )}

            {/* Agent Reports */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Enrollment Report */}
                {data.enrollment && (
                    <motion.details
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="group rounded-xl bg-[var(--bg-tertiary)]/50 border border-[var(--border-subtle)] overflow-hidden"
                    >
                        <summary className="cursor-pointer p-4 hover:bg-[var(--bg-secondary)]/30 transition-colors list-none">
                            <div className="flex items-center gap-3">
                                <UserGroupIcon className="w-6 h-6 text-blue-500 flex-shrink-0" />
                                <div className="flex-1">
                                    <h5 className="font-semibold text-[var(--text-primary)]">Enrollment</h5>
                                    <p className="text-xs text-[var(--text-tertiary)]">Feasibility Analysis</p>
                                </div>
                                <svg className="w-4 h-4 text-[var(--text-secondary)] transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </div>
                        </summary>
                        <div className="p-4 pt-2 text-sm prose prose-sm max-w-none text-[var(--text-primary)]">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.enrollment}</ReactMarkdown>
                        </div>
                    </motion.details>
                )}

                {/* Safety Report */}
                {data.safety && (
                    <motion.details
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="group rounded-xl bg-[var(--bg-tertiary)]/50 border border-[var(--border-subtle)] overflow-hidden"
                    >
                        <summary className="cursor-pointer p-4 hover:bg-[var(--bg-secondary)]/30 transition-colors list-none">
                            <div className="flex items-center gap-3">
                                <ShieldCheckIcon className="w-6 h-6 text-amber-500 flex-shrink-0" />
                                <div className="flex-1">
                                    <h5 className="font-semibold text-[var(--text-primary)]">Safety</h5>
                                    <p className="text-xs text-[var(--text-tertiary)]">Risk Assessment</p>
                                </div>
                                <svg className="w-4 h-4 text-[var(--text-secondary)] transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </div>
                        </summary>
                        <div className="p-4 pt-2 text-sm prose prose-sm max-w-none text-[var(--text-primary)]">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.safety}</ReactMarkdown>
                        </div>
                    </motion.details>
                )}

                {/* Efficacy Report */}
                {data.efficacy && (
                    <motion.details
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="group rounded-xl bg-[var(--bg-tertiary)]/50 border border-[var(--border-subtle)] overflow-hidden"
                    >
                        <summary className="cursor-pointer p-4 hover:bg-[var(--bg-secondary)]/30 transition-colors list-none">
                            <div className="flex items-center gap-3">
                                <BeakerIcon className="w-6 h-6 text-purple-500 flex-shrink-0" />
                                <div className="flex-1">
                                    <h5 className="font-semibold text-[var(--text-primary)]">Efficacy</h5>
                                    <p className="text-xs text-[var(--text-tertiary)]">Clinical Evidence</p>
                                </div>
                                <svg className="w-4 h-4 text-[var(--text-secondary)] transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </div>
                        </summary>
                        <div className="p-4 pt-2 text-sm prose prose-sm max-w-none text-[var(--text-primary)]">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.efficacy}</ReactMarkdown>
                        </div>
                    </motion.details>
                )}
            </div>
        </div>
    );
}
