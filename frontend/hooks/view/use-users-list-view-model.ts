import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { getApiBase } from "@/lib/utils";
import type { User } from "@/services/auth";

/**
 * ViewModel para a lista de usuários.
 * Gerencia a busca e remoção de usuários.
 */
export function useUsersListViewModel(initialUsers: User[] = []) {
  const [users, setUsers] = useState<User[]>(initialUsers);
  const [loading, setLoading] = useState(initialUsers.length === 0);
  const [error, setError] = useState("");

  const fetchUsers = useCallback(async () => {
    try {
      // Se já temos dados e não for um refresh explícito, poderíamos pular, 
      // mas aqui vamos manter a capacidade de recarregar.
      setLoading(true);
      const token = document.cookie
        .split("; ")
        .find((row) => row.startsWith("auth_token="))
        ?.split("=")[1];

      const res = await fetch(`${getApiBase()}/auth/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        if (res.status === 403)
          throw new Error("Acesso negado. Apenas administradores.");
        throw new Error("Falha ao carregar usuários");
      }

      const data = await res.json();
      setUsers(data);
    } catch (err: any) {
      setError(err.message || "Não foi possível carregar a lista.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Se não recebemos initialUsers, carregamos no mount.
  // Se recebemos, assumimos que já está carregado (SSR).
  useEffect(() => {
    if (initialUsers.length === 0) {
      fetchUsers();
    }
  }, [fetchUsers, initialUsers.length]);

  const handleDelete = useCallback(async (id: number) => {
    try {
      const token = document.cookie
        .split("; ")
        .find((row) => row.startsWith("auth_token="))
        ?.split("=")[1];

      const res = await fetch(`${getApiBase()}/auth/users/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Erro ao excluir");
      }

      // Atualiza a lista localmente removendo o item
      setUsers((prev) => prev.filter((u) => u.id !== id));
      toast.success("Usuário removido.");
    } catch (err: any) {
      toast.error(err.message);
    }
  }, []);

  return {
    users,
    loading,
    error,
    handleDelete,
    refresh: fetchUsers
  };
}
