import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, User } from '../services/api';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, fullName?: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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
