import { useState, useCallback, useEffect } from "react";
import { toast } from "sonner";
import { getApiBase } from "@/lib/utils";

type AuthUser = { id: number; email: string; name: string; role: string };

/**
 * Hook de Autenticação.
 * Gerencia login, registro, logout e persistência de sessão (localStorage + Cookies).
 * Sincroniza o estado do usuário entre abas via localStorage.
 */
export default function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  /**
   * Realiza o login do usuário.
   * Define o cookie de autenticação para middleware e salva estado local.
   */
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
      toast.success("Login realizado com sucesso");
      return u;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha no login";
      setError(msg);
      toast.error(msg);
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
      toast.success("Cadastro realizado com sucesso");
      return true;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha no cadastro";
      setError(msg);
      toast.error(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Encerra a sessão do usuário.
   * Remove cookies e limpa o estado.
   */
  const logout = useCallback(() => {
    document.cookie = `auth_token=; path=/; max-age=0`;
    setUser(null);
    toast.success("Sessão encerrada");
  }, []);

  useEffect(() => {
    try {
      const raw = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
      if (raw) {
        const parsed = JSON.parse(raw) as AuthUser;
        if (parsed && parsed.email) {
          setUser(parsed);
        }
      }
    } catch {}
  }, []);

  useEffect(() => {
    try {
      if (user) {
        window.localStorage.setItem("auth_user", JSON.stringify(user));
      } else {
        window.localStorage.removeItem("auth_user");
      }
    } catch {}
  }, [user]);

  return { loading, error, user, login, register, logout };
}
