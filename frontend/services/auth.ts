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
 * Converte respostas de erro (FastAPI) em mensagens amigáveis.
 * - FastAPI 422 costuma vir com: { detail: [{ loc, msg, type }, ...] }
 * - Outros erros podem vir com: { detail: "..." }
 */
async function extractApiErrorMessage(
  res: Response,
  fallback: string
): Promise<string> {
  // Tenta JSON
  try {
    const data: any = await res.json();

    // detail como array (422 validation)
    if (Array.isArray(data?.detail)) {
      const msgs = data.detail
        .map((e: any) => (typeof e?.msg === "string" ? e.msg : null))
        .filter(Boolean) as string[];

      if (msgs.length > 0) {
        // remove duplicadas
        const unique = Array.from(new Set(msgs));
        return unique.join("\n");
      }
    }

    // detail como string
    if (typeof data?.detail === "string" && data.detail.trim()) {
      return data.detail.trim();
    }

    // mensagem alternativa comum
    if (typeof data?.message === "string" && data.message.trim()) {
      return data.message.trim();
    }
  } catch {
    // ignora
  }

  // Tenta texto puro (caso backend retorne plain text)
  try {
    const txt = await res.text();
    if (txt && txt.trim()) return txt.trim();
  } catch {
    // ignora
  }

  return fallback;
}

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
     */
    async validateInvite(token: string) {
      const res = await client.fetch(
        `${baseUrl}/auth/validate-invite/${token}`,
        { cache: "no-store" }
      );

      if (!res.ok) {
        const msg = await extractApiErrorMessage(res, "Convite inválido");
        throw new Error(msg);
      }

      return res.json();
    },

    /**
     * Finaliza o registro de um novo usuário a partir de um convite.
     * Endpoint: POST /auth/register-invite
     */
    async registerInvite(payload: RegisterInvitePayload) {
      const res = await client.fetch(`${baseUrl}/auth/register-invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        // Aqui é onde vai aparecer: "Senha fraca: incluir letra minúscula", etc.
        const msg = await extractApiErrorMessage(res, "Erro ao criar conta");
        throw new Error(msg);
      }
    },

    /**
     * Lista todos os usuários cadastrados (Requer privilégios de Admin).
     * Endpoint: GET /auth/users
     */
    async getUsers(token: string) {
      const res = await client.fetch(`${baseUrl}/auth/users`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });

      if (!res.ok) {
        if (res.status === 403) throw new Error("Acesso negado");
        const msg = await extractApiErrorMessage(res, "Falha ao carregar usuários");
        throw new Error(msg);
      }

      return res.json();
    },

    /**
     * Envia um convite por e-mail para um novo usuário (Requer privilégios de Admin).
     * Endpoint: POST /auth/invite
     */
    async inviteUser(email: string, token: string) {
      const res = await client.fetch(`${baseUrl}/auth/invite`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const msg = await extractApiErrorMessage(res, "Erro ao enviar convite");
        throw new Error(msg);
      }
    },

    /**
     * Remove um usuário do sistema (Requer privilégios de Admin).
     * Endpoint: DELETE /auth/users/{userId}
     */
    async deleteUser(userId: number, token: string) {
      const res = await client.fetch(`${baseUrl}/auth/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const msg = await extractApiErrorMessage(res, "Erro ao remover usuário");
        throw new Error(msg);
      }
    },
  };
}
