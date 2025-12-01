'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '@/services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    // Load user on mount
    useEffect(() => {
        const loadUser = async () => {
            try {
                const token = authService.getToken();
                if (token) {
                    const currentUser = await authService.getCurrentUser();
                    if (currentUser) {
                        setUser(currentUser);
                        setIsAuthenticated(true);
                    } else {
                        // Token invalid, clear it
                        authService.removeToken();
                        setUser(null);
                        setIsAuthenticated(false);
                    }
                }
            } catch (error) {
                console.error('Failed to load user:', error);
                authService.removeToken();
                setUser(null);
                setIsAuthenticated(false);
            } finally {
                setIsLoading(false);
            }
        };

        loadUser();
    }, []);

    const register = async (email, password, name) => {
        try {
            const { user: newUser } = await authService.register(email, password, name);
            setUser(newUser);
            setIsAuthenticated(true);
            return newUser;
        } catch (error) {
            throw error;
        }
    };

    const login = async (email, password) => {
        try {
            const { user: loggedInUser } = await authService.login(email, password);
            setUser(loggedInUser);
            setIsAuthenticated(true);
            return loggedInUser;
        } catch (error) {
            throw error;
        }
    };

    const logout = () => {
        authService.logout();
        setUser(null);
        setIsAuthenticated(false);
    };

    const value = {
        user,
        isAuthenticated,
        isLoading,
        register,
        login,
        logout,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
