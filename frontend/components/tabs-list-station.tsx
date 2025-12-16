"use client";

import { TabsList, TabsTrigger } from "@/ui/tabs";

/**
 * Propriedades da Lista de Abas de Estações.
 */
interface TabsStationProps {
  /** Lista de estações com chave e rótulo */
  stations?: {
    key: string;
    label: string;
  }[];
  /** Classes CSS adicionais para o container */
  className?: string;
  /** Classes CSS adicionais para os botões (triggers) */
  triggerClassName?: string;
}

/**
 * Componente que renderiza a lista de abas para seleção de estações.
 * Gera os triggers do componente Tabs do shadcn/ui.
 * 
 * @component
 */
export default function TabsListStation({
  stations = [],
  className = "",
  triggerClassName = "",
}: TabsStationProps) {
  // Componente: lista de abas de estações
  // Props: stations (chave/label), classes opcionais
  // Retorno: triggers de Tabs para selecionar estação ativa
  return (
    <TabsList
      className={`w-full mb-4 flex flex-wrap h-auto gap-1 ${className}`}
    >
      {stations.map(({ key, label }) => (
        <TabsTrigger
          key={key}
          value={key}
          className={`gap-2 data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-primary transition-all ${triggerClassName}`}
        >
          {label}
        </TabsTrigger>
      ))}
    </TabsList>
  );
}
