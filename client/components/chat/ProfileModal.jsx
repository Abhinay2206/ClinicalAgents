'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    XMarkIcon,
    UserCircleIcon,
    EnvelopeIcon,
    CalendarIcon,
    PencilIcon
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';

export default function ProfileModal({ isOpen, onClose }) {
    const { user } = useAuth();
    const [isEditing, setIsEditing] = useState(false);
    const [editedName, setEditedName] = useState(user?.name || '');

    const getInitials = (name) => {
        if (!name) return 'U';
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const handleSave = () => {
        // TODO: Implement save functionality
        setIsEditing(false);
    };

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
                        <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden">
                            {/* Header */}
                            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-tertiary)]">
                                <h2 className="text-xl font-semibold text-[var(--text-primary)]">Profile</h2>
                                <button
                                    onClick={onClose}
                                    className="p-2 rounded-lg hover:bg-[var(--bg-secondary)] transition-all duration-150"
                                >
                                    <XMarkIcon className="w-5 h-5 text-[var(--text-secondary)]" />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="p-6">
                                {/* Avatar Section */}
                                <div className="flex flex-col items-center mb-8">
                                    <div className="relative mb-4">
                                        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[var(--accent-teal)] to-[var(--accent-secondary)] flex items-center justify-center text-white text-3xl font-bold shadow-xl">
                                            {getInitials(user?.name || user?.email)}
                                        </div>
                                        <button className="absolute bottom-0 right-0 p-2 bg-[var(--accent-teal)] rounded-full shadow-lg hover:bg-[var(--accent-secondary)] transition-all duration-150">
                                            <PencilIcon className="w-4 h-4 text-white" />
                                        </button>
                                    </div>

                                    {!isEditing ? (
                                        <div className="text-center">
                                            <h3 className="text-2xl font-bold text-[var(--text-primary)] mb-1">
                                                {user?.name || 'User'}
                                            </h3>
                                            <p className="text-sm text-[var(--text-secondary)]">{user?.email}</p>
                                        </div>
                                    ) : (
                                        <div className="w-full max-w-sm">
                                            <input
                                                type="text"
                                                value={editedName}
                                                onChange={(e) => setEditedName(e.target.value)}
                                                className="w-full px-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] text-center focus:outline-none focus:border-[var(--accent-teal)] transition-all"
                                                placeholder="Your name"
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Profile Information */}
                                <div className="space-y-4 mb-6">
                                    <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg flex items-center gap-4">
                                        <div className="p-3 bg-[var(--bg-secondary)] rounded-lg">
                                            <UserCircleIcon className="w-6 h-6 text-[var(--accent-teal)]" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-xs text-[var(--text-secondary)] mb-1">Full Name</p>
                                            <p className="text-sm font-medium text-[var(--text-primary)]">
                                                {user?.name || 'Not set'}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg flex items-center gap-4">
                                        <div className="p-3 bg-[var(--bg-secondary)] rounded-lg">
                                            <EnvelopeIcon className="w-6 h-6 text-[var(--accent-teal)]" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-xs text-[var(--text-secondary)] mb-1">Email Address</p>
                                            <p className="text-sm font-medium text-[var(--text-primary)]">
                                                {user?.email}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg flex items-center gap-4">
                                        <div className="p-3 bg-[var(--bg-secondary)] rounded-lg">
                                            <CalendarIcon className="w-6 h-6 text-[var(--accent-teal)]" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-xs text-[var(--text-secondary)] mb-1">Member Since</p>
                                            <p className="text-sm font-medium text-[var(--text-primary)]">
                                                {formatDate(user?.createdAt)}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Statistics */}
                                <div className="grid grid-cols-3 gap-4 mb-6">
                                    <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg text-center">
                                        <p className="text-2xl font-bold text-[var(--accent-teal)] mb-1">0</p>
                                        <p className="text-xs text-[var(--text-secondary)]">Chats</p>
                                    </div>
                                    <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg text-center">
                                        <p className="text-2xl font-bold text-[var(--accent-teal)] mb-1">0</p>
                                        <p className="text-xs text-[var(--text-secondary)]">Messages</p>
                                    </div>
                                    <div className="p-4 bg-[var(--bg-tertiary)] rounded-lg text-center">
                                        <p className="text-2xl font-bold text-[var(--accent-teal)] mb-1">0</p>
                                        <p className="text-xs text-[var(--text-secondary)]">Days Active</p>
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex gap-3">
                                    {isEditing ? (
                                        <>
                                            <button
                                                onClick={handleSave}
                                                className="flex-1 py-3 px-4 bg-gradient-to-r from-[var(--accent-teal)] to-[var(--accent-secondary)] text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-150"
                                            >
                                                Save Changes
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setIsEditing(false);
                                                    setEditedName(user?.name || '');
                                                }}
                                                className="flex-1 py-3 px-4 bg-[var(--bg-tertiary)] text-[var(--text-primary)] font-semibold rounded-lg hover:bg-[var(--bg-secondary)] transition-all duration-150"
                                            >
                                                Cancel
                                            </button>
                                        </>
                                    ) : (
                                        <button
                                            onClick={() => setIsEditing(true)}
                                            className="flex-1 py-3 px-4 bg-gradient-to-r from-[var(--accent-teal)] to-[var(--accent-secondary)] text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-150"
                                        >
                                            Edit Profile
                                        </button>
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
