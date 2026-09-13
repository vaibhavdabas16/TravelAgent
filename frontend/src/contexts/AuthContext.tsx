import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, User } from '../services/api';
import { toast } from 'sonner';
import { migrateLocalTripsToAccount } from '../lib/saved-trips';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, fullName?: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Hand any trips saved before signing in to the account.
 *
 * Without this, signing in would appear to lose them: the trips list reads
 * from the account once authenticated, and guest trips live in localStorage.
 * Never fatal — failing to move a trip must not fail the login.
 */
async function adoptGuestTrips(): Promise<void> {
    try {
        const moved = await migrateLocalTripsToAccount();
        if (moved > 0) {
            toast.success(moved === 1 ? 'Saved your trip to your account' : `Saved ${moved} trips to your account`);
        }
    } catch {
        /* the trips stay where they are; nothing is lost */
    }
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    useEffect(() => {
        const initAuth = async () => {
            const token = api.getToken();
            if (token) {
                try {
                    api.setToken(token);
                    const userData = await api.getCurrentUser();
                    setUser(userData);
                } catch (error) {
                    console.error("Failed to restore session:", error);
                    api.setToken(null);
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, []);

    const login = async (email: string, password: string) => {
        setIsLoading(true);
        try {
            await api.login(email, password);
            const userData = await api.getCurrentUser();
            setUser(userData);
            await adoptGuestTrips();
        } finally {
            setIsLoading(false);
        }
    };

    const register = async (email: string, password: string, fullName?: string) => {
        setIsLoading(true);
        try {
            await api.register(email, password, fullName);
            const userData = await api.getCurrentUser();
            setUser(userData);
            await adoptGuestTrips();
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        api.setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{
            user,
            isAuthenticated: !!user,
            isLoading,
            login,
            register,
            logout
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
