import { cookies } from "next/headers";
import { createAuthService, type User } from "@/services/auth";
import { defaultHttpClient } from "@/services/http";
import AccessClient from "./access-client";

export default async function AccessSettingsPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get("auth_token")?.value;
  let initialUsers: User[] = [];

  if (token) {
    try {
      const authService = createAuthService(defaultHttpClient);
      initialUsers = await authService.getUsers(token);
    } catch (e) {
      console.error("Falha ao carregar usuários no servidor:", e);
      // Se falhar (ex: token inválido), passamos array vazio
      // O cliente tentará buscar novamente e lidará com erro 403 se for o caso
    }
  }

  return <AccessClient initialUsers={initialUsers} />;
}
