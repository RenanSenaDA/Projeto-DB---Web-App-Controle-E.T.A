import { createAuthService } from "@/services/auth";
import { defaultHttpClient } from "@/services/http";
import { useCallback, useState } from "react";
import { RegisterInvitePayload } from "@/services/auth";

/**
 * Hook personalizado para lógica de Autenticação de Registro.
 * Encapsula as interações com a API relacionadas ao registro de usuário e validação de convite.
 * 
 * @returns {Object} Operações e estado de autenticação
 * @returns {Function} validateInvite - Valida o token do convite
 * @returns {Function} registerUser - Finaliza o registro do usuário
 * @returns {boolean} loadingAuth - Estado de carregamento para operações de auth
 */
export function useRegisterAuth() {
  const [loadingAuth, setLoadingAuth] = useState(false);
  const authService = createAuthService(defaultHttpClient);

  const validateInvite = useCallback(async (token: string) => {
    setLoadingAuth(true);
    try {
      const res = await authService.validateInvite(token);
      return res;
    } finally {
      setLoadingAuth(false);
    }
  }, []);

  const registerUser = useCallback(async (payload: RegisterInvitePayload) => {
    setLoadingAuth(true);
    try {
      await authService.registerInvite(payload);
    } finally {
      setLoadingAuth(false);
    }
  }, []);

  return {
    validateInvite,
    registerUser,
    loadingAuth
  };
}
