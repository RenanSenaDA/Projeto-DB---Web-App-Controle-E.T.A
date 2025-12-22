"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { defaultHttpClient } from "@/services/http";

type AuthUser = {
  id: number;
  email: string;
  name?: string;
  role?: string;
};

type LoginResponse = {
  token: string;
  user: AuthUser;
};

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadUserFromStorage = useCallback(() => {
    try {
      const raw = window.localStorage.getItem("auth_user");
      if (!raw) return null;
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    const u = loadUserFromStorage();
    setUser(u);
    setLoading(false);
  }, [loadUserFromStorage]);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const res = await defaultHttpClient.fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const msg = await res.text().catch(() => "");
        throw new Error(msg || "Falha no login");
      }

      const json = (await res.json()) as LoginResponse;

      // 1) usuário
      window.localStorage.setItem("auth_user", JSON.stringify(json.user));
      setUser(json.user);

      // 2) token — CRÍTICO: o http.ts lê do localStorage
      window.localStorage.setItem("token", json.token);
      // opcional: compatibilidade com outras chaves
      window.localStorage.setItem("access_token", json.token);

      // 3) cookie opcional (se você já usava)
      document.cookie = `auth_token=${json.token}; path=/; max-age=${60 * 60 * 8};`;

      toast.success("Login realizado");
      return true;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha no login";
      toast.error(msg);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem("auth_user");
    window.localStorage.removeItem("token");
    window.localStorage.removeItem("access_token");
    window.localStorage.removeItem("jwt");

    // remove cookie (se existir)
    document.cookie = "auth_token=; path=/; max-age=0;";

    setUser(null);
    toast.success("Sessão encerrada");
  }, []);

  const isAdmin = useMemo(() => {
    return (user?.role || "").toLowerCase() === "admin";
  }, [user]);

  return { user, isAdmin, loading, login, logout };
}
