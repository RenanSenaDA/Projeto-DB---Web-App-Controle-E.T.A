"use client";
import { Toaster } from "sonner";

/**
 * Componente wrapper para o sistema de notificações (Toasts).
 * Configura o posicionamento e tema das notificações globais (Sonner).
 * 
 * @component
 */
export function AppToaster() {
  return <Toaster richColors position="top-right" />;
}
