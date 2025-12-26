import type { HttpClient } from "@/services/http";
import { getApiBase } from "@/lib/utils";

/**
 * Resposta da validação de um token de convite.
 * Retorna o e-mail associado ao convite para pré-preencher o formulário.
 */
export type InviteValidationResponse = {
  email: string;
};

/**
 * Dados necessários para concluir o cadastro via convite.
 */
export type RegisterInvitePayload = {
  /** Token único do convite recebido por e-mail */
  token: string;
  /** Nome completo do usuário */
  name: string;
  /** Senha definida pelo usuário */
  password: string;
};

/**
 * Modelo de Usuário do sistema.
 */
export interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

/**
 * Interface do serviço de autenticação e gestão de usuários.
 */
export type AuthService = {
  validateInvite: (token: string) => Promise<InviteValidationResponse>;
  registerInvite: (payload: RegisterInvitePayload) => Promise<void>;
  getUsers: (token: string) => Promise<User[]>;
  inviteUser: (email: string, token: string) => Promise<void>;
  deleteUser: (userId: number, token: string) => Promise<void>;
};

/**
 * Cria a instância do serviço de Auth.
 * @param client - Cliente HTTP para realizar as requisições.
 */
export function createAuthService(client: HttpClient): AuthService {
  const baseUrl = getApiBase();

  return {
    /**
     * Valida se um token de convite é legítimo e ainda não expirou.
     * Endpoint: GET /auth/validate-invite/{token}
     * @param token - O hash do convite.
     * @returns {Promise<InviteValidationResponse>} O e-mail associado ao convite.
     * @throws {Error} Se o convite for inválido ou expirado.
     */
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

    /**
     * Finaliza o registro de um novo usuário a partir de um convite.
     * Endpoint: POST /auth/register-invite
     * @param payload - Objeto contendo token, nome e senha.
     */
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

    /**
     * Lista todos os usuários cadastrados (Requer privilégios de Admin).
     * Endpoint: GET /auth/users
     * @param token - Token JWT do administrador logado.
     * @returns {Promise<User[]>} Lista de usuários.
     */
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

    /**
     * Envia um convite por e-mail para um novo usuário (Requer privilégios de Admin).
     * Endpoint: POST /auth/invite
     * @param email - E-mail do destinatário.
     * @param token - Token JWT do administrador logado.
     */
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

    /**
     * Remove um usuário do sistema (Requer privilégios de Admin).
     * Endpoint: DELETE /auth/users/{userId}
     * @param userId - ID do usuário a ser removido.
     * @param token - Token JWT do administrador logado.
     */
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