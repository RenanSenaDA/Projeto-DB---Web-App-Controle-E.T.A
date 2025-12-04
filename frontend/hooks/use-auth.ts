import { useState, useCallback } from "react";
import { getApiBase } from "@/lib/utils";

type AuthUser = { id: number; email: string; name: string; role: string };

export default function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${getApiBase()}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      const json = await res.json();
      const token: string = json.token;
      const u: AuthUser = json.user;
      // cookie simples para o middleware
      document.cookie = `auth_token=${token}; path=/; max-age=${60 * 60 * 8}`; // 8h
      setUser(u);
      return u;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha no login";
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${getApiBase()}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      return true;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha no cadastro";
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    document.cookie = `auth_token=; path=/; max-age=0`;
    setUser(null);
  }, []);

  return { loading, error, user, login, register, logout };
}
