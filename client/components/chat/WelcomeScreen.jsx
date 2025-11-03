'use client';

import { 
  SparklesIcon, 
  UserGroupIcon, 
  ChartBarIcon, 
  ShieldCheckIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

export default function WelcomeScreen({ onSendMessage }) {
  const examples = [
    {
      icon: UserGroupIcon,
      title: "Patient Enrollment",
      prompt: "What are the enrollment criteria for diabetes trials?"
    },
    {
      icon: ChartBarIcon,
      title: "Efficacy Analysis",
      prompt: "Show me recent efficacy results for cancer immunotherapy"
    },
    {
      icon: ShieldCheckIcon,
      title: "Safety Monitoring",
      prompt: "What are the common adverse events in cardiovascular trials?"
    },
    {
      icon: MagnifyingGlassIcon,
      title: "Trial Search",
      prompt: "Find active clinical trials for Alzheimer's disease"
    }
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full px-4 py-8 fade-in">
      {/* Logo & Title */}
      <div className="text-center mb-10">
        <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-[var(--accent-teal)] flex items-center justify-center shadow-[var(--shadow-soft)]">
          <SparklesIcon className="w-7 h-7 text-white" />
        </div>
        
        <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-2">
          ClinicalGPT
        </h1>
        
        <p className="text-[15px] text-[var(--text-secondary)] max-w-md mx-auto">
          AI assistant for clinical trial intelligence
        </p>
      </div>

      {/* Example Prompts */}
      <div className="w-full max-w-2xl">
        <h2 className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-4 text-center">
          Try asking
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => onSendMessage(example.prompt)}
              className="group p-4 rounded-xl bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] text-left transition-all duration-150 hover:shadow-[var(--shadow-soft)] border border-transparent hover:border-[var(--border-subtle)]"
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[var(--accent-teal)]/10 flex items-center justify-center flex-shrink-0 group-hover:bg-[var(--accent-teal)] transition-colors">
                  <example.icon className="w-4 h-4 text-[var(--accent-teal)] group-hover:text-white transition-colors" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-[var(--text-primary)] mb-1 text-sm">
                    {example.title}
                  </h3>
                  <p className="text-xs text-[var(--text-secondary)] line-clamp-2 leading-relaxed">
                    {example.prompt}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-10 text-center">
        <p className="text-xs text-[var(--text-tertiary)]">
          Powered by Gemini AI · Clinical research assistant
        </p>
      </div>
    </div>
  );
}
