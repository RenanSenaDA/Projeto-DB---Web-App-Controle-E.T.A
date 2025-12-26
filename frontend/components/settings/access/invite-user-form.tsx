"use client";

import { Button } from "@/ui/button";
import { Input } from "@/ui/input";
import { useInviteUserViewModel } from "@/hooks/view/use-invite-user-view-model";

/**
 * Formulário para convidar novos usuários.
 * Apenas administradores podem convidar.
 */
export function InviteUserForm() {
  const {
    email,
    setEmail,
    loading,
    handleInvite
  } = useInviteUserViewModel();

  return (
    <form onSubmit={handleInvite} className="flex flex-col sm:flex-row gap-4 sm:items-end max-w-lg">
      <div className="flex-1 space-y-2">
        <label htmlFor="invite-email" className="text-sm font-medium leading-none">
          E-mail do novo colaborador
        </label>
        <Input
          id="invite-email"
          type="email"
          placeholder="colaborador@aqualink.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <Button type="submit" disabled={loading}>
        {loading ? "Enviando..." : "Enviar Convite"}
      </Button>
    </form>
  );
}
