import { cn } from "@/lib/utils";

interface SectionLabelProps {
  title: string;
  color: string;
}

export default function SectionLabel({ title, color }: SectionLabelProps) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <div className={cn("w-1 h-5 rounded-full shadow-sm", color)} />

      <h3 className="font-semibold text-[#00283F] tracking-tight">{title}</h3>
    </div>
  );
}
