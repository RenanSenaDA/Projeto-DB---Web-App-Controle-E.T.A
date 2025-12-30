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

async function extractLoginError(res: Response): Promise<string> {
  // tenta JSON
  try {
    const data: any = await res.json();
    if (typeof data?.detail === "string" && data.detail.trim()) return data.detail.trim();
    if (typeof data?.message === "string" && data.message.trim()) return data.message.trim();
  } catch {}

  // fallback texto
  try {
    const txt = await res.text();
    if (txt && txt.trim()) return txt.trim();
  } catch {}

  return "Falha no login";
}

/**
 * Hook de Autenticação.
 * Gerencia o estado do usuário logado e operações de login/logout.
 * Persiste o token em cookie e dados não sensíveis no localStorage (UI).
 */
export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const isHttps = useCallback(() => {
    if (typeof window === "undefined") return false;
    return window.location.protocol === "https:";
  }, []);

  const setAuthCookie = useCallback(
    (token: string, maxAgeSeconds: number) => {
      const secure = isHttps() ? "; Secure" : "";
      document.cookie = `auth_token=${token}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax${secure}`;
    },
    [isHttps]
  );

  const clearAuthCookie = useCallback(() => {
    const secure = isHttps() ? "; Secure" : "";
    document.cookie = `auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax${secure}`;
  }, [isHttps]);

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

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        const res = await defaultHttpClient.fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });

        if (!res.ok) {
          const msg = await extractLoginError(res);
          throw new Error(msg);
        }

        const json = (await res.json()) as LoginResponse;

        // Segurança: valida mínimo esperado
        if (!json?.token || !json?.user?.id || !json?.user?.email) {
          throw new Error("Resposta de login inválida.");
        }

        window.localStorage.setItem("auth_user", JSON.stringify(json.user));
        setUser(json.user);

        setAuthCookie(json.token, 60 * 60 * 24);

        toast.success("Login realizado");
        return true;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Falha no login";
        toast.error(msg);
        return false;
      }
    },
    [setAuthCookie]
  );

  const logout = useCallback(() => {
    window.localStorage.removeItem("auth_user");
    window.localStorage.removeItem("token");
    window.localStorage.removeItem("auth_token");

    clearAuthCookie();

    setUser(null);
    toast.success("Sessão encerrada");
  }, [clearAuthCookie]);

  const isAdmin = useMemo(() => {
    return (user?.role || "").toLowerCase() === "admin";
  }, [user]);

  return { user, isAdmin, loading, login, logout };
}
