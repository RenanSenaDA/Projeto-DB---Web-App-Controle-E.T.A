"use client";

import { TabsList, TabsTrigger } from "@/ui/tabs";
import { Factory, Filter, Waves } from "lucide-react";

const DEFAULT_STATIONS = [
  {
    key: "eta",
    label: "ETA",
    icon: Factory,
  },
  {
    key: "ultrafiltracao",
    label: "Ultrafiltração",
    icon: Waves,
  },
  {
    key: "carvao",
    label: "Filtro Carvão",
    icon: Filter,
  },
];

interface TabsStationProps {
  stations?: {
    key: string;
    label: string;
    icon?: React.ComponentType<{ className?: string }>;
  }[];
  className?: string;
  triggerClassName?: string;
}

export default function TabsListStation({
  stations = DEFAULT_STATIONS,
  className = "",
  triggerClassName = "",
}: TabsStationProps) {
  return (
    <TabsList className={`w-full mb-4 ${className}`}>
      {stations.map(({ key, label, icon: Icon = Factory }) => (
        <TabsTrigger
          key={key}
          value={key}
          className={`gap-2 data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-[#00B4F0] ${triggerClassName}`}
        >
          <Icon className="h-4 w-4" />
          {label}
        </TabsTrigger>
      ))}
    </TabsList>
  );
}
