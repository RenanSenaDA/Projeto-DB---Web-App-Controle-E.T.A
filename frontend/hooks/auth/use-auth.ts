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

/**
 * Hook de Autenticação.
 * Gerencia o estado do usuário logado e operações de login/logout.
 * Persiste o token em cookies (seguro) e dados não sensíveis no localStorage (UI).
 */
export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Carrega apenas os dados públicos do usuário do storage para preencher a UI rapidamente
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

      // 1) Salva dados do usuário (não sensíveis) no localStorage para UI
      //    Isso é feito para preencher a UI rapidamente, mesmo sem token
      window.localStorage.setItem("auth_user", JSON.stringify(json.user));
      setUser(json.user);

      // 2) Salva o Token APENAS no Cookie
      // Max-age: 8 horas (60 * 60 * 8)
      // Secure: Só envia em HTTPS (importante para prod)
      // SameSite=Strict: Protege contra CSRF
      document.cookie = `auth_token=${json.token}; path=/; max-age=${
        60 * 60 * 8
      }; SameSite=Strict; Secure`;

      toast.success("Login realizado");
      return true;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha no login";
      toast.error(msg);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    // Limpa dados do usuário
    window.localStorage.removeItem("auth_user");

    // Limpa chaves relacionadas ao token se existirem
    window.localStorage.removeItem("token");

    // Remove o cookie definindo uma data expirada
    document.cookie =
      "auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict; Secure";

    setUser(null);
    toast.success("Sessão encerrada");
  }, []);

  const isAdmin = useMemo(() => {
    return (user?.role || "").toLowerCase() === "admin";
  }, [user]);

  return { user, isAdmin, loading, login, logout };
}
