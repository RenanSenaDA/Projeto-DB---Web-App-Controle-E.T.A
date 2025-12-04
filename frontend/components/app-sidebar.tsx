"use client";

import Image from "next/image";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { BarChart2, BarChart3, LayoutDashboard, Settings } from "lucide-react";

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
    url: "/reports",
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
      <SidebarFooter />
    </Sidebar>
  );
}
