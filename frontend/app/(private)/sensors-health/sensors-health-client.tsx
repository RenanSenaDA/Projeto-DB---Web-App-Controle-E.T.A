"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/ui/table";
import { Badge } from "@/ui/badge";
import { Button } from "@/ui/button";
import Loading from "@/components/feedback/loading";
import { RefreshCw } from "lucide-react";

import { useSensorsHealthViewModel } from "@/hooks/view/use-sensors-health-view-model";

function fmtAge(sec: number | null): string {
  if (sec === null || sec === undefined) return "—";
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec / 60)} min`;
  if (sec < 86400) return `${Math.floor(sec / 3600)} h`;
  return `${Math.floor(sec / 86400)} d`;
}

function fmtVal(v: number | null, unit: string | null): string {
  if (v === null || v === undefined) return "—";
  return unit ? `${v} ${unit}` : String(v);
}

export default function SensorsHealthClient() {
  const { items, loading, reload } = useSensorsHealthViewModel();

  const online = items.filter((i) => i.status === "online").length;
  const stale = items.filter((i) => i.status === "stale").length;
  const suspects = items.filter((i) => i.suspect).length;

  return (
    <div className="container mx-auto p-4 md:p-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-6 border-b gap-4">
        <div>
          <h2 className="text-xl font-semibold">Saúde dos Sensores</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Última leitura, tempo desde a última leitura e suspeita de leitura inválida. Atualiza
            automaticamente a cada 30s.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => reload()}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Atualizar
        </Button>
      </div>

      <div className="flex gap-3 flex-wrap mt-4">
        <Badge variant="outline">Total: {items.length}</Badge>
        <Badge className="bg-emerald-600 text-white">Online: {online}</Badge>
        <Badge variant="destructive">Mudos: {stale}</Badge>
        <Badge variant="secondary">Suspeitos: {suspects}</Badge>
      </div>

      {loading && items.length === 0 ? (
        <div className="mt-6">
          <Loading />
        </div>
      ) : (
        <div className="mt-4 bg-card rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tag</TableHead>
                <TableHead>Último valor</TableHead>
                <TableHead>Última leitura há</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Qualidade</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    Nenhum sensor com leitura.
                  </TableCell>
                </TableRow>
              ) : (
                items.map((s) => (
                  <TableRow key={s.tag}>
                    <TableCell className="font-mono text-xs">{s.tag}</TableCell>
                    <TableCell className="font-mono">
                      {fmtVal(s.last_value, s.unit)}
                      {s.suspect ? (
                        <Badge variant="destructive" className="ml-2">
                          suspeito
                        </Badge>
                      ) : null}
                    </TableCell>
                    <TableCell>{fmtAge(s.age_seconds)}</TableCell>
                    <TableCell>
                      {s.status === "online" ? (
                        <Badge className="bg-emerald-600 text-white">Online</Badge>
                      ) : (
                        <Badge variant="destructive">Mudo</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-xs">
                      {s.quality ?? "—"}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
