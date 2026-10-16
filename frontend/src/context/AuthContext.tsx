import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, UserRole } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password?: string) => Promise<boolean>;
  signup: (name: string, email: string, password: string, role: UserRole) => Promise<boolean>;
  logout: () => void;
  updateProfile: (name: string, email: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('projectpulse_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('projectpulse_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('projectpulse_user');
    }
  }, [user]);

  const login = async (email: string, password?: string): Promise<boolean> => {
    const authUser = await api.auth.login(email, password);
    setUser(authUser);
    return true;
  };

  const signup = async (name: string, email: string, password: string, role: UserRole): Promise<boolean> => {
    await api.auth.register(name, email, password, role);
    // Unverified user is created; authentication session requires verified email
    return true;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('projectpulse_user');
  };

  const updateProfile = (name: string, email: string) => {
    if (user) {
      setUser({ ...user, name, email });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
