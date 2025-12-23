import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { useRegisterAuth } from "@/hooks/auth/use-register-auth";

/**
 * ViewModel for the Registration Page.
 * Implements MVVM pattern by separating view logic from UI components.
 * 
 * Responsibilities:
 * - Manages form state (name, password, etc.)
 * - Handles token validation logic on mount
 * - Orchestrates registration flow via useRegisterAuth
 * - Manages UI states (loading, errors, navigation)
 * 
 * @returns Object containing form state, status flags, and event handlers
 */
export function useRegisterViewModel() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { validateInvite, registerUser, loadingAuth } = useRegisterAuth();

  const token = searchParams.get("token");

  // Form State
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // View State
  const [initializing, setInitializing] = useState(true);
  const [validToken, setValidToken] = useState(false);

  // Initial Validation
  useEffect(() => {
    if (!token) {
      toast.error("Token de convite não encontrado.");
      setInitializing(false);
      return;
    }

    validateInvite(token)
      .then((data) => {
        setEmail(data.email);
        setValidToken(true);
      })
      .catch((err) => {
        toast.error(err.message || "Convite inválido ou expirado.");
      })
      .finally(() => {
        setInitializing(false);
      });
  }, [token, validateInvite]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validToken || !token) return;

    if (password !== confirmPassword) {
      toast.error("As senhas não coincidem.");
      return;
    }

    if (password.length < 6) {
      toast.error("A senha deve ter pelo menos 6 caracteres.");
      return;
    }

    try {
      await registerUser({ token, name, password });
      router.push("/login?registered=1");
    } catch (err: any) {
      toast.error(err.message || "Erro ao criar conta.");
    }
  };

  const navigateToLogin = () => {
    router.push("/login");
  };

  return {
    // State
    email,
    name,
    setName,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    
    // Status
    loading: initializing || loadingAuth, // General loading state
    initializing,
    submitting: loadingAuth && !initializing, // Specific for form submission
    validToken,

    // Actions
    handleSubmit,
    navigateToLogin,
  };
}
