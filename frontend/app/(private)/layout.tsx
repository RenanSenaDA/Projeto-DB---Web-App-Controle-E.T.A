import { AppSidebar } from "@/components/app-sidebar";
import SystemStatus from "@/components/feedback/system-status";
import { SidebarProvider, SidebarTrigger } from "@/ui/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="w-full">
        <div className="p-2">
          <div className="flex items-center justify-between">
            <SidebarTrigger />
            <SystemStatus />
          </div>
          {children}
        </div>
      </main>
    </SidebarProvider>
  );
}
