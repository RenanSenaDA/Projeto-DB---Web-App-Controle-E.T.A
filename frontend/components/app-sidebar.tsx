"use client";

import Image from "next/image";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  BarChart2,
  BarChart3,
  LayoutDashboard,
  Settings,
  LogOut,
  ChevronsUpDown,
} from "lucide-react";
import { useRouter } from "next/navigation";

import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/ui/sidebar";
import { useAuth } from "@/hooks/auth/use-auth";

/**
 * Lista de itens de navegação da sidebar.
 * Cada item contém título, URL e ícone.
 */
const items = [
  {
    title: "Dashboard",
    url: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Séries Temporais",
    url: "/time-series",
    icon: BarChart3,
  },
  {
    title: "Relatórios",
    url: "/generate-reports",
    icon: BarChart2,
  },
  {
    title: "Configurações",
    url: "/settings",
    icon: Settings,
  },
];

/**
 * Componente de barra lateral (Sidebar) da aplicação.
 * Responsável pela navegação principal e exibição de informações do usuário.
 *
 * @component
 * @client Este componente roda no cliente (use client) para interatividade e acesso ao contexto de rota.
 */
export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, user } = useAuth();

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex flex-col items-center justify-center pt-2.5">
          <Image
            src="/aqualink-logo-escuro.svg"
            alt="AquaLink Logo"
            width={120}
            height={40}
            priority
            className="dark:hidden"
          />
          <Image
            src="/aqualink-logo.svg"
            alt="AquaLink Logo"
            width={120}
            height={40}
            priority
            className="hidden dark:block"
          />
          <h1 className="mt-2 text-[10px] font-bold tracking-widest text-secondary-foreground uppercase opacity-70">
            Sistema de Monitoramento
          </h1>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const isActive =
                  item.url === "/settings"
                    ? pathname?.startsWith("/settings")
                    : pathname === item.url;

                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.title}
                      className={`
                        transition-all duration-200 ease-in-out h-10 mb-1
                        ${
                          isActive
                            ? "bg-secondary text-primary hover:bg-secondary hover:text-primary font-medium"
                            : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                        }
                      `}
                    >
                      <Link href={item.url} prefetch>
                        <item.icon
                          className={
                            isActive ? "text-primary" : "text-muted-foreground"
                          }
                        />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={() => {
                logout();
                router.push("/login");
              }}
              tooltip="Sair"
              className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            >
              <LogOut />
              <span>Sair</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" className="mt-2">
              <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center overflow-hidden">
                <span className="text-xs font-medium">
                  {((user?.name || user?.email || "CN").match(/\b\w/g) || [])
                    .slice(0, 2)
                    .join("")
                    .toUpperCase()}
                </span>
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">
                  {user?.name || "Usuário"}
                </span>
                <span className="truncate text-xs">
                  {user?.email || "email"}
                </span>
              </div>
              <ChevronsUpDown className="ml-auto size-4" />
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
