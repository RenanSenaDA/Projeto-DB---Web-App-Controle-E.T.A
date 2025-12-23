import type { HttpClient } from "@/services/http";
import { getApiBase } from "@/lib/utils";

export type InviteValidationResponse = {
  email: string;
};

export type RegisterInvitePayload = {
  token: string;
  name: string;
  password: string;
};

export interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

export type AuthService = {
  validateInvite: (token: string) => Promise<InviteValidationResponse>;
  registerInvite: (payload: RegisterInvitePayload) => Promise<void>;
  getUsers: (token: string) => Promise<User[]>;
  inviteUser: (email: string, token: string) => Promise<void>;
  deleteUser: (userId: number, token: string) => Promise<void>;
};

export function createAuthService(client: HttpClient): AuthService {
  const baseUrl = getApiBase();

  return {
    async validateInvite(token: string) {
      const res = await client.fetch(
        `${baseUrl}/auth/validate-invite/${token}`,
        {
          cache: "no-store",
        }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Convite inválido");
      }
      return res.json();
    },

    async registerInvite(payload: RegisterInvitePayload) {
      const res = await client.fetch(`${baseUrl}/auth/register-invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao criar conta");
      }
    },

    async getUsers(token: string) {
      const res = await client.fetch(`${baseUrl}/auth/users`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });

      if (!res.ok) {
        if (res.status === 403) throw new Error("Acesso negado");
        throw new Error("Falha ao carregar usuários");
      }
      return res.json();
    },

    async inviteUser(email: string, token: string) {
      const res = await client.fetch(`${baseUrl}/auth/invite`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao enviar convite");
      }
    },

    async deleteUser(userId: number, token: string) {
      const res = await client.fetch(`${baseUrl}/auth/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao remover usuário");
      }
    },
  };
}
