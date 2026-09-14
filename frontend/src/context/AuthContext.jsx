import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const token = localStorage.getItem('access_token');
    if (storedUser && token) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.clear();
      }
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    const response = await api.post('/auth/login/', { username, password });
    const { access, refresh, user: userData, must_change_password } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);

    return { must_change_password, user: userData };
  };

  const logout = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        await api.post('/auth/logout/', { refresh });
      }
    } catch (e) {
      console.error('Logout error', e);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setUser(null);
      window.location.href = '/login';
    }
  };

  const hasRole = (roleName) => {
    if (!user || !user.roles) return false;
    return user.roles.some((r) => r.role__name === roleName || r.name === roleName);
  };

  const hasPermission = (permCodename) => {
    if (!user) return false;
    if (user.is_superuser) return true;
    if (!user.permissions) return false;
    return user.permissions.includes(permCodename);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasRole, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
