"use client";

import { TabsList, TabsTrigger } from "@/ui/tabs";

interface TabsStationProps {
  stations?: {
    key: string;
    label: string;
  }[];
  className?: string;
  triggerClassName?: string;
}

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
          className={`gap-2 data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-[#00B4F0] transition-all ${triggerClassName}`}
        >
          {label}
        </TabsTrigger>
      ))}
    </TabsList>
  );
}
