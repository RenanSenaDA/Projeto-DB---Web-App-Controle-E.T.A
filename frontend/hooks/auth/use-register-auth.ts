import { createAuthService } from "@/services/auth";
import { defaultHttpClient } from "@/services/http";
import { useCallback, useState } from "react";
import { RegisterInvitePayload } from "@/services/auth";

/**
 * Custom hook for Registration Authentication logic.
 * Encapsulates API interactions related to user registration and invite validation.
 * 
 * @returns {Object} Auth operations and state
 * @returns {Function} validateInvite - Validates the invitation token
 * @returns {Function} registerUser - Completes user registration
 * @returns {boolean} loadingAuth - Loading state for auth operations
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
