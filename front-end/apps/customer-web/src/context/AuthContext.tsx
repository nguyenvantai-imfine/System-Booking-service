"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

export interface CustomerUser {
  id?: number | string;
  ho_ten: string;
  email: string;
  sdt?: string;
  vai_tro?: string;
}

interface AuthContextType {
  user: CustomerUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  authModalMode: "login" | "register";
  openAuthModal: (mode?: "login" | "register") => void;
  closeAuthModal: () => void;
  login: (emailOrUsername: string, pass: string) => Promise<boolean>;
  register: (payload: {
    ten_dang_nhap: string;
    email: string;
    mat_khau: string;
    ho_ten: string;
    sdt?: string;
  }) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CustomerUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<"login" | "register">("login");

  useEffect(() => {
    try {
      const savedToken = localStorage.getItem("customer_token");
      const savedUser = localStorage.getItem("customer_user");
      if (savedToken && savedUser) {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      }
    } catch (e) {
      console.error("Error reading customer auth state", e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const openAuthModal = (mode: "login" | "register" = "login") => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const login = async (emailOrUsername: string, pass: string): Promise<boolean> => {
    try {
      const tokenRes = await apiClient.login({
        ten_dang_nhap_hoac_email: emailOrUsername,
        mat_khau: pass,
      });

      if (!tokenRes.access_token) {
        throw new Error("Không nhận được token xác thực");
      }

      const accessToken = tokenRes.access_token;
      localStorage.setItem("customer_token", accessToken);
      setToken(accessToken);

      // Extract user info from token response or getMe()
      if (tokenRes.user) {
        const u = tokenRes.user;
        const profile = u.profile || u.nguoi_dung;
        const fullName =
          profile?.ho_va_ten ||
          (profile ? [profile.ho, profile.ten].filter(Boolean).join(" ") : (u as any).ho_va_ten) ||
          u.ten_dang_nhap;

        const customerProfile: CustomerUser = {
          id: u.id_tai_khoan,
          ho_ten: fullName || u.ten_dang_nhap,
          email: u.email,
          sdt: u.sdt || undefined,
          vai_tro: u.vai_tro,
        };
        localStorage.setItem("customer_user", JSON.stringify(customerProfile));
        setUser(customerProfile);
      } else {
        try {
          const me = await apiClient.getMe();
          const profile = me.profile || me.nguoi_dung;
          const fullName =
            profile?.ho_va_ten ||
            (profile ? [profile.ho, profile.ten].filter(Boolean).join(" ") : me.ten_dang_nhap);

          const customerProfile: CustomerUser = {
            id: me.id_tai_khoan,
            ho_ten: fullName || me.ten_dang_nhap,
            email: me.email,
            sdt: me.sdt || undefined,
            vai_tro: me.vai_tro,
          };
          localStorage.setItem("customer_user", JSON.stringify(customerProfile));
          setUser(customerProfile);
        } catch {
          const fallbackProfile: CustomerUser = {
            ho_ten: emailOrUsername.split("@")[0],
            email: emailOrUsername,
          };
          localStorage.setItem("customer_user", JSON.stringify(fallbackProfile));
          setUser(fallbackProfile);
        }
      }

      setIsAuthModalOpen(false);
      return true;
    } catch (err: any) {
      console.error("Login failed:", err);
      throw err;
    }
  };

  const register = async (payload: {
    ten_dang_nhap: string;
    email: string;
    mat_khau: string;
    ho_ten: string;
    sdt?: string;
  }): Promise<boolean> => {
    try {
      // Split full name into ho and ten
      const nameParts = payload.ho_ten.trim().split(" ");
      const ho = nameParts.length > 1 ? nameParts[0] : "";
      const ten = nameParts.length > 1 ? nameParts.slice(1).join(" ") : nameParts[0];

      await apiClient.register({
        ten_dang_nhap: payload.ten_dang_nhap,
        email: payload.email,
        mat_khau: payload.mat_khau,
        ho,
        ten,
        sdt: payload.sdt,
        vai_tro: "CUSTOMER",
      });

      // Tự động đăng nhập sau khi đăng ký thành công
      await login(payload.ten_dang_nhap, payload.mat_khau);
      return true;
    } catch (err: any) {
      console.error("Register failed:", err);
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem("customer_token");
    localStorage.removeItem("customer_user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        isAuthModalOpen,
        authModalMode,
        openAuthModal,
        closeAuthModal,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
