# Frontend AquaLink

Aplicação web desenvolvida com **Next.js 15 (App Router)** e **TypeScript**, focada no monitoramento de estações de tratamento de água/esgoto. O sistema é projetado para ser **White Label Ready**, altamente performático e arquiteturalmente desacoplado seguindo o padrão **MVVM (Model-View-ViewModel)**.

## 🚀 Tecnologias Principais

- **Framework**: Next.js 15 (App Router)
- **Linguagem**: TypeScript (Strict Mode)
- **Estilização**: Tailwind CSS (com variáveis CSS para temas)
- **Componentes**: Shadcn/ui (Radix UI)
- **Gráficos**: Recharts
- **Ícones**: Lucide React
- **HTTP Client**: Fetch API com abstração customizada

## 🏛️ Arquitetura e Padrões

O projeto segue rigorosos filtros de qualidade:

1.  **Atomização & SOLID**: Componentes pequenos, reutilizáveis e com responsabilidade única.
2.  **Desacoplamento (MVVM)**: Separação clara entre UI (View) e Lógica (ViewModel).
    - **View**: Componentes React em `app/` e `components/`. Apenas renderizam dados.
    - **ViewModel**: Custom Hooks em `hooks/view/`. Gerenciam estado, regras de negócio da tela e chamadas à API.
    - **Model**: Interfaces em `types/` e Serviços em `services/`.
3.  **Next.js Performance**:
    - Uso intensivo de **Server Components** para o shell da aplicação.
    - **Client Components** apenas onde há interatividade (hooks, eventos).
    - Carregamento de dados otimizado e estratégias de cache.
4.  **White Label Ready**:
    - Zero uso de cores Hexadecimais hardcoded (`#ffffff`).
    - Uso exclusivo de classes semânticas do Tailwind (`bg-primary`, `text-muted-foreground`) mapeadas para variáveis CSS (`globals.css`).
    - Script de validação `npm run check-hex` para garantir conformidade.

## 📂 Estrutura de Pastas

```
frontend/
├── app/                  # Rotas (Next.js App Router)
│   ├── (private)/        # Rotas protegidas (Dashboard, Settings, etc.)
│   ├── (public)/         # Rotas públicas (Login, Register)
│   └── layout.tsx        # Layout raiz
├── components/           # Componentes de UI (Negócio)
│   ├── feedback/         # Loadings, Error States, Empty States
│   ├── kpi/              # Cards e visualizações de KPI
│   └── ...
├── hooks/                # Lógica da Aplicação
│   ├── api/              # Hooks de integração de dados (Data Fetching)
│   ├── auth/             # Hooks de autenticação
│   ├── ui/               # Hooks de interface (responsividade, etc)
│   └── view/             # View Models (Lógica específica de cada página)
├── lib/                  # Utilitários puros (formatadores, helpers)
├── services/             # Camada de Infraestrutura HTTP
├── types/                # Definições de Tipos TypeScript
└── ui/                   # Componentes Base (Shadcn/ui - Botões, Inputs, etc.)
```

## 🔄 Fluxos de Dados

### 1. Dashboard (`/dashboard`)
- **Carregamento**: Busca payload inicial via `useApi`.
- **Dinamismo**: As abas de estações e seções de categorias são geradas dinamicamente baseadas no JSON retornado.
- **ViewModel**: `useDashboardViewModel` processa os dados brutos para separar KPIs por estação e categoria.

### 2. Séries Temporais (`/time-series`)
- **Lazy Loading**: O gráfico só busca dados quando o usuário seleciona uma estação/categoria.
- **Otimização**: Usa `cache: 'no-store'` para garantir dados realtime, mas faz cache local de navegação.
- **ViewModel**: `useTimeSeriesViewModel` gerencia o filtro de data, seleção de estação e busca de pontos.

### 3. Relatórios (`/generate-reports`)
- **Geração**: Permite selecionar KPIs e datas.
- **Download**: O backend gera um Excel (blob) que é baixado pelo navegador.
- **Arquitetura**: Separação entre estado do formulário (`useReportViewModel`) e ação de gerar (`useReportGenerate`).

### 4. Configurações (`/settings`)
- **Gerenciamento**: Permite definir limites (máximos) para KPIs e ativar/desativar alarmes globais.
- **Feedback**: Feedback otimista e notificações via `sonner` (Toast).

## 🛠️ Scripts Disponíveis

- `npm run dev`: Inicia servidor de desenvolvimento.
- `npm run build`: Build de produção.
- `npm run start`: Inicia servidor de produção.
- `npm run lint`: Verifica erros de linting.
- **`npm run check-hex`**: Verifica se existem cores hexadecimais hardcoded nos arquivos (essencial para White Label).

## 🎨 Temas e Estilização

A personalização é feita via variáveis CSS em `styles/globals.css`. Para mudar o tema (cores de um cliente específico), basta alterar os valores das variáveis HSL (`--primary`, `--secondary`, etc.), sem tocar no código React.

---
**Desenvolvido com foco em Manutenibilidade, Performance e Escalabilidade.**
