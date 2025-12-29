# Frontend Aqualink

Interface web moderna e responsiva para o sistema de monitoramento de estações de tratamento de água (Aqualink EQ). Desenvolvida com **Next.js 16**, **TypeScript** e **Tailwind CSS v4**, a aplicação segue o padrão arquitetural **MVVM (Model-View-ViewModel)** para garantir desacoplamento, testabilidade e manutenibilidade.

## 🚀 Tecnologias Principais

*   **Framework**: [Next.js 16](https://nextjs.org/) (App Router)
*   **Linguagem**: [TypeScript](https://www.typescriptlang.org/) (Strict Mode)
*   **Estilização**: [Tailwind CSS v4](https://tailwindcss.com/)
*   **Componentes UI**: [Shadcn/ui](https://ui.shadcn.com/) (baseado em Radix UI)
*   **Visualização de Dados**: [Recharts](https://recharts.org/)
*   **Ícones**: [Lucide React](https://lucide.dev/)
*   **Notificações**: [Sonner](https://sonner.emilkowal.ski/)

## 🏛️ Arquitetura e Padrões

O projeto adota uma arquitetura limpa e escalável, focada na separação de responsabilidades:

### Padrão MVVM (Model-View-ViewModel)

1.  **Model**:
    *   Definições de tipos em `types/`.
    *   Serviços de comunicação com a API em `services/`.
    *   Responsável apenas pela estrutura dos dados e chamadas HTTP puras.

2.  **View**:
    *   Componentes React localizados em `app/` (Páginas) e `components/` (UI).
    *   Focam exclusivamente na renderização e interação visual.
    *   Não contêm lógica de negócios complexa ou chamadas diretas à API.

3.  **ViewModel**:
    *   Custom Hooks localizados em `hooks/view/`.
    *   Atuam como a ponte entre Model e View.
    *   Gerenciam o estado local, efeitos colaterais (side effects), formatação de dados para exibição e regras de negócio da interface.

### White Label Ready

O sistema foi projetado para ser facilmente customizável (White Label):
*   **Cores Semânticas**: Não utilizamos cores hexadecimais hardcoded (`#ffffff`, `#000000`) nos componentes.
*   **Variáveis CSS**: Todas as cores são definidas em `styles/globals.css` usando variáveis CSS nativas mapeadas pelo Tailwind.
*   **Validação Automática**: O script `npm run lint:colors` verifica a existência de cores proibidas no código.

## 📂 Estrutura de Pastas

```
frontend/
├── app/                    # Next.js App Router (Rotas e Páginas)
│   ├── (private)/          # Rotas protegidas (Dashboard, Configurações, etc.)
│   ├── (public)/           # Rotas públicas (Login, Registro)
│   ├── layout.tsx          # Layout raiz da aplicação
|   ├── page.tsx            # Página Inicial da aplicação (Login)
├── components/             # Componentes Reutilizáveis
│   ├── feedback/           # Loaders, Mensagens de Erro, Empty States
│   ├── forms/              # Formulários (Login, Registro)
│   ├── kpi/                # Componentes específicos de indicadores (Cards, Gráficos)
│   ├── settings/           # Componentes das telas de configuração
│   ├── generate-reports/   # Componentes para geração de relatórios
|   └── ...                 # Outros componentes reutilizáveis
├── hooks/                  # Lógica da Aplicação (Hooks)
│   ├── api/                # Hooks de Data Fetching (useApi, useSeries, use-report-generate)
│   ├── auth/               # Hooks de Autenticação (Login, Logout, Register)
│   ├── ui/                 # Hooks de UI (Responsividade)
│   └── view/               # ViewModels (Lógica específica de cada página)
├── lib/                    # Utilitários puros (Formatadores de data/número)
├── services/               # Camada de Serviço (HTTP Client, Endpoints)
├── types/                  # Definições de Tipos TypeScript (Interfaces)
├── ui/                     # Componentes Base do Design System (Botões, Inputs, Cards)
└── scripts/                # Scripts auxiliares de manutenção
```

## ⚙️ Configuração

A aplicação pode ser configurada através de variáveis de ambiente. Crie um arquivo `.env.local` na raiz do projeto `frontend/` se precisar sobrescrever os padrões:

```env
# URL base da API Backend
# Se não definido, o sistema tenta inferir:
# 1. Browser: http://{hostname}:8000
# 2. Server-side (Docker): http://api:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🚀 Instalação e Execução

Certifique-se de ter o **Node.js** (versão 18 ou superior) instalado.

1.  **Instale as dependências:**

    ```bash
    npm install
    ```

2.  **Execute o servidor de desenvolvimento:**

    ```bash
    npm run dev
    ```

    A aplicação estará disponível em `http://localhost:3000`.

3.  **Build de Produção:**

    ```bash
    npm run build
    npm run start
    ```

## � Scripts Disponíveis

*   `npm run dev`: Inicia o servidor de desenvolvimento com Hot Reload.
*   `npm run build`: Cria a versão otimizada para produção.
*   `npm run start`: Inicia o servidor de produção (requer build prévio).
*   `npm run lint`: Executa a verificação estática de código (ESLint).
*   `npm run lint:colors`: Executa o script de validação de cores para garantir conformidade com White Label.

## 📱 Funcionalidades Principais

### Dashboard (`/dashboard`)
Visão geral em tempo real das estações de tratamento.
*   Exibição de KPIs categorizados (Qualidade, Operacional).
*   Alertas visuais baseados em limites configuráveis.
*   Atualização dinâmica de dados.

### Séries Temporais (`/time-series`)
Análise histórica de dados de KPIs.
*   Gráficos interativos com seleção de período e sensores.
*   Filtros dinâmicos por tag.

### Relatórios (`/generate-reports`)
Exportação de dados.
*   Geração de planilhas Excel (.xlsx).
*   Filtros por período pré-definido ou intervalo personalizado.

### Configurações (`/settings`)
Gestão do sistema.
*   **Controle de Acesso**: Convidar e listagem de usuários (Admin).
*   **Alarmes**: Configuração de limites operacionais para KPIs.

---
**Desenvolvido com foco em Manutenibilidade, Performance e Escalabilidade.**
