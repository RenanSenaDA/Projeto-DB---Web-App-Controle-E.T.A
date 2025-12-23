"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { InviteUserForm } from "@/components/settings/access/invite-user-form";
import { UsersList } from "@/components/settings/access/users-list";
import SectionLabel from "@/components/label-section";
import type { User } from "@/services/auth";
import { UserPlus2 } from "lucide-react";
import { useAuth } from "@/hooks/auth/use-auth";
import Loading from "@/components/feedback/loading";

interface AccessClientProps {
  initialUsers?: User[];
}

export default function AccessClient({ initialUsers }: AccessClientProps) {
  const { isAdmin, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAdmin) {
      router.replace("/settings/alarms");
    }
  }, [loading, isAdmin, router]);

  if (loading) {
    return <Loading />;
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="space-y-8">
      <div className="pb-6 border-b">
        <h2 className="text-xl font-semibold text-foreground mb-1 flex items-center gap-2">
          <UserPlus2 className="w-6 h-6 text-primary" />
          Convidar Colaborador
        </h2>
        <p className="text-sm text-muted-foreground">
          Envie um link de convite seguro para adicionar novos membros à equipe
          de colaboradores.
        </p>
      </div>

      <div className="bg-muted/50 p-4 md:p-6 rounded-xl border border-dashed border-border">
        <InviteUserForm />
      </div>

      <div className="pt-4">
        <div className="mb-6">
          <SectionLabel title="Usuários Ativos" color="bg-primary" />
        </div>

        <UsersList initialUsers={initialUsers} />
      </div>
    </div>
  );
}
