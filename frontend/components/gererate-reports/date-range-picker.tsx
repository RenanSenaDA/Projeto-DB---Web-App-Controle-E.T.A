/**
 * Propriedades do Seletor de Intervalo de Datas.
 */
interface DateRangePickerProps {
  /** Data inicial (string YYYY-MM-DD) */
  start: string;
  /** Data final (string YYYY-MM-DD) */
  end: string;
  /** Callback para alteração da data inicial */
  onStartChange: (val: string) => void;
  /** Callback para alteração da data final */
  onEndChange: (val: string) => void;
}

/**
 * Componente para seleção de período (data de início e fim).
 * Renderiza dois inputs nativos de data com estilização consistente.
 * 
 * @component
 */
export default function DateRangePicker({
  start,
  end,
  onStartChange,
  onEndChange,
}: DateRangePickerProps) {
  return (
    <div className="bg-card p-6 rounded-xl border border-border shadow-sm">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground">
            Data Inicial
          </label>
          <input
            type="date"
            value={start}
            onChange={(e) => onStartChange(e.target.value)}
            className="w-full p-2.5 rounded-lg border border-input bg-muted/50 text-foreground focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground">
            Data Final
          </label>
          <input
            type="date"
            value={end}
            onChange={(e) => onEndChange(e.target.value)}
            className="w-full p-2.5 rounded-lg border border-input bg-muted/50 text-foreground focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all"
          />
        </div>
      </div>
    </div>
  );
}
