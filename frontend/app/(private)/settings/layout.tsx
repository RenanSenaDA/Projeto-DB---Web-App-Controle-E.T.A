"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import PageHeader from "@/components/header-page";
import { BellRing, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/auth/use-auth";

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAdmin } = useAuth();

  return (
    <div className="container mx-auto p-4 md:p-6">
      <PageHeader
        title="Configurações do Sistema"
        subtitle="Gerencie alarmes, usuários e permissões"
      />

      <div className="mt-6 md:mt-8 flex flex-col lg:flex-row gap-6 md:gap-8">
        {/* Sidebar de Navegação */}
        <aside className="w-full lg:w-64 shrink-0">
          <nav className="flex flex-row lg:flex-col lg:pt-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <SettingsLink
              href="/settings/alarms"
              label="Alarmes & Limites"
              icon={<BellRing className="w-4 h-4" />}
            />
            {isAdmin && (
              <SettingsLink
                href="/settings/access"
                label="Gestão de Acesso"
                icon={<Users className="w-4 h-4" />}
              />
            )}
          </nav>
        </aside>

        {/* Área de Conteúdo */}
        <main className="flex-1 bg-white p-4 md:p-8 rounded-xl border border-slate-200 shadow-sm min-h-[500px]">
          {children}
        </main>
      </div>
    </div>
  );
}

// Componente auxiliar para link ativo
function SettingsLink({
  href,
  label,
  icon,
}: {
  href: string;
  label: string;
  icon: React.ReactNode;
}) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all duration-200",
        "flex-1 justify-center lg:flex-none lg:justify-start lg:w-full",
        "border-b-[3px] border-l-0 lg:border-b-0 lg:border-l-[3px]",
        isActive
          ? "border-primary bg-slate-50 text-primary"
          : "border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900"
      )}
    >
      {icon}
      {label}
    </Link>
  );
}
