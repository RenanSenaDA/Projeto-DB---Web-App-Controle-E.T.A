"use client";

import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

export interface RegisterFormProps {
  /** O endereço de e-mail associado ao token do convite (somente leitura) */
  email: string;
  /** O valor do campo nome completo */
  name: string;
  /** Callback para alteração do nome */
  onNameChange: (val: string) => void;
  /** O valor do campo senha */
  password: string;
  /** Callback para alteração da senha */
  onPasswordChange: (val: string) => void;
  /** O valor do campo confirmação de senha */
  confirmPassword: string;
  /** Callback para alteração da confirmação de senha */
  onConfirmPasswordChange: (val: string) => void;
  /** Handler de envio do formulário */
  onSubmit: (e: React.FormEvent) => void;
  /** Flag indicando se o registro está em andamento */
  submitting: boolean;
  /** Flag indicando se o token do convite é válido */
  validToken: boolean;
  /** Callback para navegar de volta para a página de login */
  onNavigateToLogin: () => void;
  /** Flag indicando se a validação do token está em andamento */
  initializing: boolean;
}

/**
 * Componente RegisterForm
 * 
 * Componente de UI puro responsável por renderizar o formulário de registro.
 * Gerencia:
 * - Exibição do estado de carregamento durante a validação do token
 * - Exibição de estado de erro para tokens inválidos
 * - Campos de formulário para detalhes do usuário
 * - Feedback visual de validação (via estado da UI)
 */
export function RegisterForm({
  email,
  name,
  onNameChange,
  password,
  onPasswordChange,
  confirmPassword,
  onConfirmPasswordChange,
  onSubmit,
  submitting,
  validToken,
  onNavigateToLogin,
  initializing
}: RegisterFormProps) {

  if (initializing) {
    return <div className="text-center">Validando convite...</div>;
  }

  if (!validToken) {
    return (
      <div className="text-center text-red-500">
        <p className="mb-4">Este convite é inválido ou já foi utilizado.</p>
        <Button variant="link" onClick={onNavigateToLogin}>
          Voltar para Login
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium">E-mail</label>
        <Input value={email} disabled className="bg-muted" />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Nome Completo</label>
        <Input
          placeholder="Seu nome"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Senha</label>
        <Input
          type="password"
          placeholder="******"
          value={password}
          onChange={(e) => onPasswordChange(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Confirmar Senha</label>
        <Input
          type="password"
          placeholder="******"
          value={confirmPassword}
          onChange={(e) => onConfirmPasswordChange(e.target.value)}
          required
        />
      </div>

      <Button type="submit" className="w-full" disabled={submitting}>
        {submitting ? "Criando conta..." : "Criar Conta"}
      </Button>
    </form>
  );
}
