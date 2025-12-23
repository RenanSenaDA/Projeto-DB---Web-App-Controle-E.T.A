import { useState, useCallback } from "react";
import { toast } from "sonner";
import { getApiBase } from "@/lib/utils";

/**
 * ViewModel para o formulário de convite de usuários.
 * Gerencia o estado do formulário e a comunicação com a API de convites.
 */
export function useInviteUserViewModel() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleInvite = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    try {
      const token = document.cookie
        .split("; ")
        .find((row) => row.startsWith("auth_token="))
        ?.split("=")[1];

      const res = await fetch(`${getApiBase()}/auth/invite`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Erro ao enviar convite");
      }

      toast.success(`Convite enviado para ${email}`);
      setEmail("");
    } catch (err: any) {
      toast.error(err.message || "Falha ao enviar convite");
    } finally {
      setLoading(false);
    }
  }, [email]);

  return {
    email,
    setEmail,
    loading,
    handleInvite
  };
}
