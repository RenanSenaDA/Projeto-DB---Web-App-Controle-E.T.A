"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { defaultHttpClient } from "@/services/http";

type AuthUser = {
  id: number;
  email: string;
  name?: string;
  role?: string;
  is_active?: boolean;
};

type LoginResponse = {
  token: string;
  user: AuthUser;
};

async function extractLoginError(res: Response): Promise<string> {
  try {
    const data: any = await res.json();
    if (typeof data?.detail === "string" && data.detail.trim()) return data.detail.trim();
    if (typeof data?.message === "string" && data.message.trim()) return data.message.trim();
  } catch {}
  try {
    const txt = await res.text();
    if (txt && txt.trim()) return txt.trim();
  } catch {}
  return "Falha no login";
}

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

  const clearSession = useCallback(
    (redirectToLogin: boolean) => {
      try {
        window.localStorage.removeItem("auth_user");
        window.localStorage.removeItem("token");
      } catch {}
      clearAuthCookie();
      setUser(null);

      if (redirectToLogin && typeof window !== "undefined") {
        if (!window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
      }
    },
    [clearAuthCookie]
  );

  /**
   * ✅ Boot-check: valida token no backend via /auth/me
   * Se falhar, limpa sessão e REDIRECIONA imediatamente pro /login.
   */
  useEffect(() => {
    const boot = async () => {
      try {
        const token = window.localStorage.getItem("token");
        if (!token) {
          // sem token -> não está logado
          setUser(null);
          setLoading(false);
          return;
        }

        const res = await defaultHttpClient.fetch("/auth/me", { cache: "no-store" });

        if (!res.ok) {
          clearSession(true);
          setLoading(false);
          return;
        }

        const me = (await res.json()) as AuthUser;

        if (!me?.id || !me?.email || me.is_active === false) {
          clearSession(true);
          setLoading(false);
          return;
        }

        window.localStorage.setItem("auth_user", JSON.stringify(me));
        setUser(me);
        setLoading(false);
      } catch {
        clearSession(true);
        setLoading(false);
      }
    };

    boot();
  }, [clearSession]);

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
          // ❗garante que qualquer tentativa falha não deixa “resto” de sessão
          clearSession(false);
          throw new Error(msg);
        }

        const json = (await res.json()) as LoginResponse;

        if (!json?.token || !json?.user?.id || !json?.user?.email) {
          clearSession(false);
          throw new Error("Resposta de login inválida.");
        }

        window.localStorage.setItem("token", json.token);
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
    [setAuthCookie, clearSession]
  );

  const logout = useCallback(() => {
    clearSession(true);
    toast.success("Sessão encerrada");
  }, [clearSession]);

  const isAdmin = useMemo(() => {
    return (user?.role || "").toLowerCase() === "admin";
  }, [user]);

  return { user, isAdmin, loading, login, logout };
}
