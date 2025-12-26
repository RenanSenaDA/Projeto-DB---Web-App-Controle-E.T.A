import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { useRegisterAuth } from "@/hooks/auth/use-register-auth";

/**
 * ViewModel para a Página de Registro.
 * Implementa o padrão MVVM separando a lógica de visualização dos componentes de UI.
 * 
 * Responsabilidades:
 * - Gerencia o estado do formulário (nome, senha, etc.)
 * - Lida com a lógica de validação do token na montagem
 * - Orquestra o fluxo de registro via useRegisterAuth
 * - Gerencia estados da UI (carregamento, erros, navegação)
 * 
 * @returns Objeto contendo estado do formulário, flags de status e manipuladores de eventos
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
