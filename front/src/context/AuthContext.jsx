import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

// Simple in-app credentials (no JWT needed for now)
const CREDENTIALS = {
  admin: { password: 'admin123', role: 'admin', name: 'Admin' },
  delegates: [
    { username: 'ava', password: 'ava123', role: 'delegate', name: 'Ava' },
    { username: 'youssef', password: 'youssef123', role: 'delegate', name: 'Youssef' },
    { username: 'leila', password: 'leila123', role: 'delegate', name: 'Leila' },
  ]
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const loginAdmin = (password) => {
    if (password === CREDENTIALS.admin.password) {
      setUser({ role: 'admin', name: 'Admin' });
      return true;
    }
    return false;
  };

  const loginDelegate = (username, password) => {
    const found = CREDENTIALS.delegates.find(
      d => d.username === username && d.password === password
    );
    if (found) {
      setUser({ role: 'delegate', name: found.name, username: found.username });
      return true;
    }
    return false;
  };

  const loginDoctor = (name) => {
    setUser({ role: 'doctor', name: name || 'Dr. Guest' });
    return true;
  };

  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, loginAdmin, loginDelegate, loginDoctor, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
