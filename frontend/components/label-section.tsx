import { cn } from "@/lib/utils";

interface SectionLabelProps {
  title: string;
  color: string;
  titleClassName?: string;
}

export default function SectionLabel({ title, color, titleClassName = "" }: SectionLabelProps) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <div className={cn("w-1 h-5 rounded-full shadow-sm", color)} />

      <h3 className={cn("font-semibold tracking-tight", titleClassName || "text-slate-900")}>{title}</h3>
    </div>
  );
}
