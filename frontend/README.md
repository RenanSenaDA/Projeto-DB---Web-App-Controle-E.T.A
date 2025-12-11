# Frontend AquaLink

Aplicação web construída com Next.js e TypeScript para monitorar KPIs por estação. O frontend é totalmente dinâmico: novas estações e categorias no JSON da API aparecem automaticamente nas páginas.

## Início Rápido

- Rodar desenvolvimento: `npm run dev` e acessar `http://localhost:3000`.
- Login: `http://localhost:3000/login`.
- Navegação: menu lateral com Dashboard, Séries Temporais, Relatórios e Configurações.

## Arquitetura

- Páginas (`app/(private)`):
  - `dashboard/page.tsx`: visão geral dos KPIs por estação/categoria.
  - `time-series/page.tsx`: gráficos históricos por estação/categoria.
  - `generate-reports/page.tsx`: geração de relatórios Excel.
  - `settings/page.tsx`: limites de KPIs e controle de alarmes.
- Componentes (`components`):
  - `kpi/*`: cartões, seções, filtro e visualização de séries.
  - `feedback/*`: estados de carregamento e erro.
  - `tabs-list-station.tsx`: lista de abas de estações dinâmica.
- Hooks (`hooks`):
  - `use-api.ts`: carrega o payload do dashboard e expõe utilitários.
  - `use-series.ts`: busca séries temporais para tags em um intervalo.
- Services (`services`):
  - `dashboard.ts`, `measurements.ts`, `limits.ts`, `reports.ts`: chamadas HTTP com cliente injetável.
- Utils (`lib/utils.ts`):
  - `buildCategoryMap`: mapeia categorias para título e cor.
  - `idToTag`: converte `id` com `_` para tag com `/` (compatível com API).
- UI (`ui/*`):
  - Abstrações de Tabs, Card, Chart, etc., usando Tailwind e Recharts.

## Fluxo de Dados

- Dashboard:
  - Carrega `ApiResponse` e deriva `stationKeys` dinamicamente.
  - Renderiza seções por `category` via `buildCategoryMap`.
- Séries Temporais:
  - Monta `activeTags` da estação ativa; quando há KPIs filtradas, envia apenas essas tags.
  - Chama `/measurements/series?tags=...&minutes=...` com `no-store` para dados atuais.
  - Converte pontos em labels `HH:MM` para o gráfico.
- Configurações:
  - Inicializa limites a partir de todas as KPIs e persiste via `/limits`.
- Relatórios:
  - Gera Excel opcionalmente filtrando por tags selecionadas e intervalo de datas.

## Dinamismo (Estações e Categorias)

- Estações: derivadas de `data.data` sem nomes fixos; abas são construídas a partir de `stationKeys`.
- Categorias: encontradas dinamicamente com `buildCategoryMap`, que define título e cor.
- KPIs: listas são consolidadas dinamicamente, evitando duplicação por estação.

## Estilização e Gráficos

- Tailwind CSS com `clsx` e `tailwind-merge` para compor classes.
- Recharts com `ChartContainer`/`ChartTooltip` para tema e tooltip.

## Variáveis de Ambiente

- `NEXT_PUBLIC_API_BASE_URL`: URL base do backend; fallback `http://localhost:8000`.

## Scripts

- `dev`: inicia servidor de desenvolvimento.
- `lint`: executa ESLint sobre o projeto.

## Convenções de Código

- TypeScript com `strict` e paths `@/*`.
- `HttpClient` injetável para facilitar testes/mudança de implementação.
- `idToTag`: padroniza conversão de `id` para tag da API.

## Tratamento de Erros

- Hooks expõem `error` e `loading` e notificam com `toast` quando aplicável.
- Páginas exibem `Loading` e `Error` com ações de retry.

## Extensão

- Novas estações/categorias: basta retornar no JSON da API; UI se adapta.
