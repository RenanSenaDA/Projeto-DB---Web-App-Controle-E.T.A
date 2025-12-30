import { createAuthService } from "@/services/auth";
import { defaultHttpClient } from "@/services/http";
import { useCallback, useMemo, useState } from "react";
import type { RegisterInvitePayload } from "@/services/auth";

/**
 * Hook personalizado para lógica de Autenticação de Registro.
 * Encapsula as interações com a API relacionadas ao registro de usuário e validação de convite.
 */
export function useRegisterAuth() {
  const [loadingAuth, setLoadingAuth] = useState(false);

  // Garante instância estável e evita recriar serviço a cada render
  const authService = useMemo(() => createAuthService(defaultHttpClient), []);

  const validateInvite = useCallback(
    async (token: string) => {
      setLoadingAuth(true);
      try {
        return await authService.validateInvite(token);
      } finally {
        setLoadingAuth(false);
      }
    },
    [authService]
  );

  const registerUser = useCallback(
    async (payload: RegisterInvitePayload) => {
      setLoadingAuth(true);
      try {
        await authService.registerInvite(payload);
      } finally {
        setLoadingAuth(false);
      }
    },
    [authService]
  );

  return {
    validateInvite,
    registerUser,
    loadingAuth,
  };
}
