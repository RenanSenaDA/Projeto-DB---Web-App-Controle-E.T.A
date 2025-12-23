import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, SidebarTrigger } from "@/ui/sidebar";
import { ModeToggle } from "@/components/mode-toggle";

/**
 * Layout para rotas privadas (Dashboard, Configurações, etc.).
 * Inclui a Sidebar de navegação e o SidebarProvider.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="w-full relative">
        <div className="absolute top-2 right-4 z-50">
          <ModeToggle />
        </div>
        <div className="p-2">
          <SidebarTrigger />
          {children}
        </div>
      </main>
    </SidebarProvider>
  );
}
