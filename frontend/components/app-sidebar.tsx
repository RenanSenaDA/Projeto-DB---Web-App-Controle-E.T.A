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
import useAuth from "@/hooks/use-auth";

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
          />
          <h1 className="mt-2 text-[10px] font-bold tracking-widest text-[#00283F] uppercase opacity-70">
            Sistema de Monitoramento
          </h1>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const isActive = pathname === item.url;

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
                            ? "bg-[#00283F] text-[#00B4F0] hover:bg-[#00283F] hover:text-[#00B4F0] font-medium"
                            : "text-slate-500 hover:bg-[#00B4F0]/10 hover:text-[#00283F]"
                        }
                      `}
                    >
                      <Link href={item.url} prefetch>
                        <item.icon
                          className={
                            isActive ? "text-[#00B4F0]" : "text-slate-400"
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
              className="text-slate-500 hover:bg-rose-50 hover:text-red-500"
            >
              <LogOut />
              <span>Sair</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" className="mt-2">
              <div className="h-8 w-8 rounded-lg bg-slate-200 flex items-center justify-center overflow-hidden">
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
