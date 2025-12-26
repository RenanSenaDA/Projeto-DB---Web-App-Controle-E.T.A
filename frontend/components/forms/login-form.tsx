"use client";

import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

export interface LoginFormProps {
  /** Valor do campo de e-mail */
  email: string;
  /** Callback para alteração do e-mail */
  onEmailChange: (val: string) => void;
  /** Valor do campo de senha */
  password: string;
  /** Callback para alteração da senha */
  onPasswordChange: (val: string) => void;
  /** Handler de envio do formulário */
  onSubmit: (e: React.FormEvent) => void;
  /** Flag indicando se a requisição está em andamento */
  loading: boolean;
  /** Flag indicando se o formato do e-mail é válido */
  isValidEmail: boolean;
}

/**
 * LoginForm Component
 * * Componente de UI puro responsável por renderizar o formulário de login.
 */
export function LoginForm({
  email,
  onEmailChange,
  password,
  onPasswordChange,
  onSubmit,
  loading,
  isValidEmail,
}: LoginFormProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Input
        type="email"
        placeholder="E-mail"
        value={email}
        onChange={(e) => onEmailChange(e.target.value)}
        required
      />

      <Input
        type="password"
        placeholder="Senha"
        value={password}
        onChange={(e) => onPasswordChange(e.target.value)}
        required
      />

      <Button
        type="submit"
        className="w-full bg-primary dark:text-secondary"
        disabled={loading || !isValidEmail}
      >
        Entrar
      </Button>
    </form>
  );
}