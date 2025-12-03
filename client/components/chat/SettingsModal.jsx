'use client';

import { useState } from 'react';
import {
    XMarkIcon,
    BellIcon,
    CommandLineIcon,
    InformationCircleIcon,
    PaintBrushIcon
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';

export default function SettingsModal({ isOpen, onClose }) {
    const [activeTab, setActiveTab] = useState('general');

    const tabs = [
        { id: 'general', label: 'General', icon: PaintBrushIcon },
        { id: 'notifications', label: 'Notifications', icon: BellIcon },
        { id: 'shortcuts', label: 'Shortcuts', icon: CommandLineIcon },
        { id: 'about', label: 'About', icon: InformationCircleIcon }
    ];

    const shortcuts = [
        { keys: ['Cmd', 'K'], description: 'Quick search' },
        { keys: ['Cmd', 'N'], description: 'New chat' },
        { keys: ['Cmd', ','], description: 'Open settings' },
        { keys: ['Esc'], description: 'Close modal' }
    ];

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ duration: 0.2 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4"
                    >
                        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden">
                            {/* Header */}
                            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-tertiary)]">
                                <h2 className="text-xl font-semibold text-[var(--text-primary)]">Settings</h2>
                                <button
                                    onClick={onClose}
                                    className="p-2 rounded-lg hover:bg-[var(--bg-secondary)] transition-all duration-150"
                                >
                                    <XMarkIcon className="w-5 h-5 text-[var(--text-secondary)]" />
                                </button>
                            </div>

                            <div className="flex h-[calc(85vh-80px)]">
                                {/* Sidebar Tabs */}
                                <div className="w-48 border-r border-[var(--border-subtle)] bg-[var(--bg-tertiary)] p-3">
                                    {tabs.map((tab) => (
                                        <button
                                            key={tab.id}
                                            onClick={() => setActiveTab(tab.id)}
                                            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-150 mb-1 ${activeTab === tab.id
                                                ? 'bg-[var(--accent-teal)] text-white'
                                                : 'text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]'
                                                }`}
                                        >
                                            <tab.icon className="w-5 h-5" />
                                            <span className="text-sm font-medium">{tab.label}</span>
                                        </button>
                                    ))}
                                </div>

                                {/* Content Area */}
                                <div className="flex-1 overflow-y-auto p-6">
                                    {activeTab === 'general' && (
                                        <div className="space-y-6">
                                            <div>
                                                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Appearance</h3>
                                                <div className="space-y-4">
                                                    <div className="flex items-center justify-between p-4 bg-[var(--bg-tertiary)] rounded-lg">
                                                        <div>
                                                            <p className="text-sm font-medium text-[var(--text-primary)]">Theme</p>
                                                            <p className="text-xs text-[var(--text-secondary)] mt-1">Currently using dark mode</p>
                                                        </div>
                                                        <div className="px-3 py-1.5 bg-[var(--bg-secondary)] rounded-lg text-xs font-medium text-[var(--text-primary)]">
                                                            Dark
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div>
                                                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Language</h3>
                                                <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg">
                                                    <select className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-teal)] transition-all">
                                                        <option>English</option>
                                                        <option>Spanish</option>
                                                        <option>French</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === 'notifications' && (
                                        <div className="space-y-4">
                                            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Notification Preferences</h3>

                                            {['Email notifications', 'Push notifications', 'Sound alerts', 'Desktop notifications'].map((item, index) => (
                                                <div key={index} className="flex items-center justify-between p-4 bg-[var(--bg-tertiary)] rounded-lg">
                                                    <p className="text-sm font-medium text-[var(--text-primary)]">{item}</p>
                                                    <label className="relative inline-flex items-center cursor-pointer">
                                                        <input type="checkbox" className="sr-only peer" defaultChecked={index < 2} />
                                                        <div className="w-11 h-6 bg-[var(--bg-secondary)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--accent-teal)]"></div>
                                                    </label>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {activeTab === 'shortcuts' && (
                                        <div className="space-y-4">
                                            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Keyboard Shortcuts</h3>

                                            {shortcuts.map((shortcut, index) => (
                                                <div key={index} className="flex items-center justify-between p-4 bg-[var(--bg-tertiary)] rounded-lg">
                                                    <p className="text-sm text-[var(--text-primary)]">{shortcut.description}</p>
                                                    <div className="flex gap-2">
                                                        {shortcut.keys.map((key, keyIndex) => (
                                                            <kbd
                                                                key={keyIndex}
                                                                className="px-3 py-1.5 bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-lg text-xs font-semibold text-[var(--text-primary)] shadow-sm"
                                                            >
                                                                {key}
                                                            </kbd>
                                                        ))}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {activeTab === 'about' && (
                                        <div className="space-y-6">
                                            <div className="text-center py-8">
                                                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[var(--accent-teal)] to-[var(--accent-secondary)] flex items-center justify-center">
                                                    <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                                    </svg>
                                                </div>
                                                <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">ClinicalAgent</h3>
                                                <p className="text-sm text-[var(--text-secondary)] mb-1">Version 1.0.0</p>
                                                <p className="text-xs text-[var(--text-tertiary)]">© 2024 ClinicalAgent. All rights reserved.</p>
                                            </div>

                                            <div className="space-y-3">
                                                <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg">
                                                    <p className="text-sm font-medium text-[var(--text-primary)] mb-1">Documentation</p>
                                                    <a href="#" className="text-xs text-[var(--accent-teal)] hover:underline">View documentation →</a>
                                                </div>
                                                <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg">
                                                    <p className="text-sm font-medium text-[var(--text-primary)] mb-1">Support</p>
                                                    <a href="#" className="text-xs text-[var(--accent-teal)] hover:underline">Contact support →</a>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
