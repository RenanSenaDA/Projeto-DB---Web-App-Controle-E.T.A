"use client";

import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

export interface RegisterFormProps {
  /** The email address associated with the invite token (read-only) */
  email: string;
  /** The user's full name input value */
  name: string;
  /** Callback for name input changes */
  onNameChange: (val: string) => void;
  /** The password input value */
  password: string;
  /** Callback for password input changes */
  onPasswordChange: (val: string) => void;
  /** The password confirmation input value */
  confirmPassword: string;
  /** Callback for password confirmation input changes */
  onConfirmPasswordChange: (val: string) => void;
  /** Form submission handler */
  onSubmit: (e: React.FormEvent) => void;
  /** Flag indicating if the registration is in progress */
  submitting: boolean;
  /** Flag indicating if the invite token is valid */
  validToken: boolean;
  /** Callback to navigate back to login page */
  onNavigateToLogin: () => void;
  /** Flag indicating if the token validation is in progress */
  initializing: boolean;
}

/**
 * RegisterForm Component
 * 
 * A pure UI component responsible for rendering the registration form.
 * It handles:
 * - Loading state display during token validation
 * - Error state display for invalid tokens
 * - Form fields for user details
 * - Visual validation feedback (via UI state)
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
