'use client';

import { GoogleOAuthProvider } from '@react-oauth/google';

export default function GoogleOAuthWrapper({ children }) {
    // Get Google Client ID from environment variable
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

    if (!clientId) {
        console.warn('⚠️ NEXT_PUBLIC_GOOGLE_CLIENT_ID not set. Google OAuth will not work.');
    }

    return (
        <GoogleOAuthProvider clientId={clientId}>
            {children}
        </GoogleOAuthProvider>
    );
}
