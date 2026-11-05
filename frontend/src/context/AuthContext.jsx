import React, { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("hireai_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("hireai_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem("hireai_token");
      if (storedToken) {
        try {
          const res = await api.get("/auth/me");
          const userData = {
            id: res.data.id,
            email: res.data.email,
            full_name: res.data.full_name,
            role: res.data.role,
            organization_id: res.data.organization_id,
            organization_name: res.data.organization?.name || "Apex Staffing Solutions"
          };
          setUser(userData);
          localStorage.setItem("hireai_user", JSON.stringify(userData));
        } catch (err) {
          console.error("Auth session expired", err);
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const res = await api.post("/auth/login", { email, password });
    const { access_token, user_id, full_name, role, organization_id, organization_name } = res.data;
    
    const userData = {
      id: user_id,
      email,
      full_name,
      role,
      organization_id,
      organization_name
    };

    localStorage.setItem("hireai_token", access_token);
    localStorage.setItem("hireai_user", JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem("hireai_token");
    localStorage.removeItem("hireai_user");
    setToken(null);
    setUser(null);
  };

  const isRecruiter = user?.role === "recruiter" || user?.role === "admin";
  const isClient = user?.role === "client_hiring_manager";

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isAuthenticated: !!token && !!user,
        isRecruiter,
        isClient,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

