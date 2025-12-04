interface DateRangePickerProps {
  start: string;
  end: string;
  onStartChange: (val: string) => void;
  onEndChange: (val: string) => void;
}

export default function DateRangePicker({
  start,
  end,
  onStartChange,
  onEndChange,
}: DateRangePickerProps) {
  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-600">
            Data Inicial
          </label>
          <input
            type="date"
            value={start}
            onChange={(e) => onStartChange(e.target.value)}
            className="w-full p-2.5 rounded-lg border border-slate-300 bg-slate-50 text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-600">
            Data Final
          </label>
          <input
            type="date"
            value={end}
            onChange={(e) => onEndChange(e.target.value)}
            className="w-full p-2.5 rounded-lg border border-slate-300 bg-slate-50 text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          />
        </div>
      </div>
    </div>
  );
}
