import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Token management
const TOKEN_KEY = 'clinical_agent_token';
const USER_KEY = 'clinical_agent_user';

class AuthService {
    // Get stored token
    getToken() {
        if (typeof window !== 'undefined') {
            return localStorage.getItem(TOKEN_KEY);
        }
        return null;
    }

    // Set token
    setToken(token) {
        if (typeof window !== 'undefined') {
            localStorage.setItem(TOKEN_KEY, token);
        }
    }

    // Remove token
    removeToken() {
        if (typeof window !== 'undefined') {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
        }
    }

    // Get stored user
    getUser() {
        if (typeof window !== 'undefined') {
            const userStr = localStorage.getItem(USER_KEY);
            if (userStr) {
                try {
                    return JSON.parse(userStr);
                } catch (e) {
                    return null;
                }
            }
        }
        return null;
    }

    // Set user
    setUser(user) {
        if (typeof window !== 'undefined') {
            localStorage.setItem(USER_KEY, JSON.stringify(user));
        }
    }

    // Register new user
    async register(email, password, name) {
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/register`, {
                email,
                password,
                name,
            });

            const { access_token, user } = response.data;

            // Store token and user
            this.setToken(access_token);
            this.setUser(user);

            return { token: access_token, user };
        } catch (error) {
            console.error('Registration error:', error);

            if (error.response?.data?.detail) {
                throw new Error(error.response.data.detail);
            }

            throw new Error(error.message || 'Failed to register. Please try again.');
        }
    }

    // Login user
    async login(email, password) {
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/login`, {
                email,
                password,
            });

            const { access_token, user } = response.data;

            // Store token and user
            this.setToken(access_token);
            this.setUser(user);

            return { token: access_token, user };
        } catch (error) {
            console.error('Login error:', error);

            if (error.response?.data?.detail) {
                throw new Error(error.response.data.detail);
            }

            throw new Error(error.message || 'Failed to login. Please try again.');
        }
    }

    // Logout user
    logout() {
        this.removeToken();
    }

    // Get current user from server
    async getCurrentUser() {
        try {
            const token = this.getToken();
            if (!token) {
                return null;
            }

            const response = await axios.get(`${API_BASE_URL}/auth/me`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            const user = response.data;
            this.setUser(user);
            return user;
        } catch (error) {
            console.error('Get current user error:', error);

            // If unauthorized, clear token
            if (error.response?.status === 401) {
                this.removeToken();
            }

            return null;
        }
    }

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    }

    // Login with Google OAuth
    async loginWithGoogle(credential) {
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/google`, {
                credential,
            });

            const { access_token, user } = response.data;

            // Store token and user
            this.setToken(access_token);
            this.setUser(user);

            return { token: access_token, user };
        } catch (error) {
            console.error('Google OAuth error:', error);

            if (error.response?.data?.detail) {
                throw new Error(error.response.data.detail);
            }

            throw new Error(error.message || 'Failed to authenticate with Google. Please try again.');
        }
    }
}

export const authService = new AuthService();

