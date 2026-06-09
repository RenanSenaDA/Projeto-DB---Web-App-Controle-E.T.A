"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/ui/table";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";
import { Badge } from "@/ui/badge";
import Loading from "@/components/feedback/loading";
import { Save, Check } from "lucide-react";

import {
  useAlarmsViewModel,
  type StatusFilter,
} from "@/hooks/view/use-alarms-view-model";

function fmtTs(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

function fmtNum(n: number | null): string {
  return n === null || n === undefined ? "—" : String(n);
}

const KIND_LABEL: Record<string, string> = {
  high: "Acima",
  low: "Abaixo",
  stale: "Sem leitura",
};
const STATUS_LABEL: Record<string, string> = {
  open: "Aberto",
  acked: "Reconhecido",
  resolved: "Resolvido",
};

function kindBadge(kind: string) {
  const variant: "destructive" | "outline" = kind === "stale" ? "outline" : "destructive";
  return <Badge variant={variant}>{KIND_LABEL[kind] ?? kind}</Badge>;
}

function statusBadge(status: string) {
  const variant: "destructive" | "secondary" | "outline" =
    status === "open" ? "destructive" : status === "acked" ? "secondary" : "outline";
  return <Badge variant={variant}>{STATUS_LABEL[status] ?? status}</Badge>;
}

const FILTERS: { key: StatusFilter; label: string }[] = [
  { key: "", label: "Todos" },
  { key: "open", label: "Abertos" },
  { key: "acked", label: "Reconhecidos" },
  { key: "resolved", label: "Resolvidos" },
];

export default function AlarmsClient() {
  const {
    events,
    loadingEvents,
    statusFilter,
    acking,
    ackEvent,
    changeFilter,
    limits,
    loadingLimits,
    drafts,
    savingTag,
    setDraft,
    saveRange,
  } = useAlarmsViewModel();

  return (
    <div className="container mx-auto p-4 md:p-6">
      <div className="pb-6 border-b">
        <h2 className="text-xl font-semibold">Alarmes</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Histórico de eventos e faixas de alarme (mínimo/máximo) por tag.
        </p>
      </div>

      <Tabs defaultValue="historico" className="mt-6">
        <TabsList>
          <TabsTrigger value="historico">Histórico</TabsTrigger>
          <TabsTrigger value="faixas">Faixas</TabsTrigger>
        </TabsList>

        {/* ----------------- HISTÓRICO ----------------- */}
        <TabsContent value="historico" className="mt-4">
          <div className="flex gap-2 mb-4 flex-wrap">
            {FILTERS.map((f) => (
              <Button
                key={f.key || "all"}
                size="sm"
                variant={statusFilter === f.key ? "default" : "outline"}
                onClick={() => changeFilter(f.key)}
              >
                {f.label}
              </Button>
            ))}
          </div>

          {loadingEvents ? (
            <Loading />
          ) : (
            <div className="bg-card rounded-xl border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Abertura</TableHead>
                    <TableHead>Tag</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Valor</TableHead>
                    <TableHead>Limite</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Ação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {events.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        Nenhum alarme registrado.
                      </TableCell>
                    </TableRow>
                  ) : (
                    events.map((ev) => (
                      <TableRow key={ev.id}>
                        <TableCell className="whitespace-nowrap">{fmtTs(ev.opened_at)}</TableCell>
                        <TableCell className="font-mono text-xs">{ev.tag}</TableCell>
                        <TableCell>{kindBadge(ev.kind)}</TableCell>
                        <TableCell className="font-mono">{fmtNum(ev.value)}</TableCell>
                        <TableCell className="font-mono">{fmtNum(ev.threshold)}</TableCell>
                        <TableCell>{statusBadge(ev.status)}</TableCell>
                        <TableCell className="text-right">
                          {ev.status === "open" ? (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={acking === ev.id}
                              onClick={() => ackEvent(ev.id)}
                            >
                              {acking === ev.id ? (
                                "..."
                              ) : (
                                <>
                                  <Check className="w-3 h-3 mr-1" />
                                  Reconhecer
                                </>
                              )}
                            </Button>
                          ) : null}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        {/* ----------------- FAIXAS ----------------- */}
        <TabsContent value="faixas" className="mt-4">
          {loadingLimits ? (
            <Loading />
          ) : (
            <div className="bg-card rounded-xl border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tag</TableHead>
                    <TableHead>Rótulo</TableHead>
                    <TableHead>Mínimo</TableHead>
                    <TableHead>Máximo</TableHead>
                    <TableHead className="text-right">Ação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {limits.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                        Nenhuma tag com faixa cadastrada.
                      </TableCell>
                    </TableRow>
                  ) : (
                    limits.map((l) => {
                      const d = drafts[l.tag] ?? {};
                      return (
                        <TableRow key={l.tag}>
                          <TableCell className="font-mono text-xs">{l.tag}</TableCell>
                          <TableCell>
                            <Input
                              className="w-40"
                              placeholder="(opcional)"
                              value={(d.label ?? "") as string}
                              onChange={(e) => setDraft(l.tag, "label", e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <Input
                              type="number"
                              className="w-28 text-right"
                              placeholder="—"
                              value={d.limite_min ?? ""}
                              onChange={(e) => setDraft(l.tag, "limite_min", e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <Input
                              type="number"
                              className="w-28 text-right"
                              placeholder="—"
                              value={d.limite_max ?? ""}
                              onChange={(e) => setDraft(l.tag, "limite_max", e.target.value)}
                            />
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              size="icon"
                              disabled={savingTag === l.tag}
                              onClick={() => saveRange(l.tag)}
                              title="Salvar faixa"
                            >
                              {savingTag === l.tag ? (
                                <span className="animate-spin h-4 w-4 border-2 border-current rounded-full" />
                              ) : (
                                <Save className="w-4 h-4" />
                              )}
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
              <p className="text-xs text-muted-foreground p-4">
                Defina o limite <b>Mínimo</b> e/ou <b>Máximo</b>. Deixe em branco para não alarmar
                naquele lado. Aparecem aqui as tags que já têm alguma faixa cadastrada.
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
