'use client';

import { SparklesIcon, BeakerIcon, ChartBarIcon } from '@heroicons/react/24/outline';

export default function WelcomeScreen({ onSendMessage }) {
    const exampleQueries = [
        {
            icon: SparklesIcon,
            title: "Trial Prediction",
            query: "(1) drug: Metformin; (2) disease: Type 2 Diabetes; (3) inclusion criteria: Adults 18-65; (4) exclusion criteria: Kidney disease;",
            description: "Predict trial outcome"
        },
        {
            icon: BeakerIcon,
            title: "Safety Analysis",
            query: "What are the safety concerns with aspirin?",
            description: "Check drug safety"
        },
        {
            icon: ChartBarIcon,
            title: "Enrollment Data",
            query: "What is the enrollment success rate for diabetes trials?",
            description: "Historical success rates"
        }
    ];

    return (
        <div className="h-full flex items-center justify-center px-6">
            <div className="max-w-2xl w-full space-y-8 fade-in">
                {/* Welcome Header */}
                <div className="text-center space-y-3">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--accent-teal)] to-[var(--accent-secondary)] mb-4">
                        <SparklesIcon className="w-8 h-8 text-white" />
                    </div>

                    <h1 className="text-3xl font-bold text-[var(--text-primary)]">
                        Welcome to ClinicalAgent 2.0
                    </h1>

                    <p className="text-[var(--text-secondary)] text-sm max-w-md mx-auto">
                        AI-powered clinical trial outcome prediction and analysis. Ask questions or predict trial success using our numbered format.
                    </p>
                </div>

                {/* Example Queries */}
                <div className="grid gap-3">
                    <p className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wide">
                        Try these examples
                    </p>

                    {exampleQueries.map((example, index) => (
                        <button
                            key={index}
                            onClick={() => onSendMessage(example.query)}
                            className="group text-left p-4 rounded-xl bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] hover:border-[var(--accent-teal)]/30 transition-all duration-200 hover:shadow-[var(--shadow-soft)]"
                        >
                            <div className="flex items-start gap-3">
                                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-[var(--accent-teal)]/10 group-hover:bg-[var(--accent-teal)]/20 flex items-center justify-center transition-colors">
                                    <example.icon className="w-5 h-5 text-[var(--accent-teal)]" />
                                </div>

                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                                            {example.title}
                                        </h3>
                                        <span className="text-xs text-[var(--text-tertiary)]">
                                            {example.description}
                                        </span>
                                    </div>

                                    <p className="text-xs text-[var(--text-secondary)] line-clamp-2">
                                        {example.query}
                                    </p>
                                </div>
                            </div>
                        </button>
                    ))}
                </div>

                {/* Info Banner */}
                <div className="p-4 rounded-lg bg-[var(--accent-teal)]/10 border border-[var(--accent-teal)]/20">
                    <p className="text-xs text-[var(--text-secondary)] text-center">
                        💡 <strong>Pro tip:</strong> Use numbered format for trial predictions: <code className="px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] font-mono text-[10px]">(1) drug: ... (2) disease: ...</code>
                    </p>
                </div>
            </div>
        </div>
    );
}
