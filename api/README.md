# Aqualink API

API para monitoramento e gestão de qualidade da água (Aqualink EQ). Desenvolvida em Python com FastAPI, esta aplicação fornece endpoints para visualização de dados em tempo real, gestão de usuários, autenticação e geração de relatórios.

## Estrutura do Projeto

A estrutura do diretório `api/` é organizada da seguinte forma:

```
api/
├── core/               # Configurações globais e segurança
│   ├── config.py       # Variáveis de ambiente e configurações (Settings)
│   └── security.py     # Hashing e verificação de senhas
├── database/           # Conexão com o banco de dados
│   └── connection.py   # Configuração do SQLAlchemy
├── routers/            # Rotas da API (Endpoints)
│   └── auth.py         # Autenticação, login e gestão de usuários
│   └── dashboard.py    # Dados para o dashboard em tempo real
│   └── reports.py      # Geração de relatórios Excel
│   └── alarms.py       # Ativação e Desativalção dos alarmes
│   └── limits.py       # Retorno e Atualização dos Limites
│   └── measurements.py # Recupera séries temporais de medições para os sensores especificados.
├── schemas/            # Modelos Pydantic para validação de dados
│   ├── auth.py         # Schemas de login e usuário
│   ├── dashboard.py    # Schemas de KPI e resposta do dashboard
│   ├── alarms.py       # Schemas de Alarmes
│   ├── limits.py       # Schemas de Limites
│   ├── measurements.py # Schemas de Medições
├── services/           # Lógica de negócios e serviços externos
│   ├── email_service.py # Envio de e-mails via Brevo
│   └── report_service.py # Geração de planilhas Excel com Pandas
├── deps.py             # Dependências (Injeção de dependência)
├── main.py             # Ponto de entrada da aplicação
├── requirements.txt    # Dependências do projeto
└── Dockerfile          # Configuração para containerização
```

## Configuração

A aplicação utiliza variáveis de ambiente para configuração. Crie um arquivo `.env` na raiz do diretório `api/` com as seguintes variáveis:

```env
# Banco de Dados
DATABASE_URL=postgresql+psycopg://usuario:senha@host:porta/banco

# Aplicação
LOCAL_TZ=America/Fortaleza
FEED_INTERVAL=5
FRONTEND_URL=http://localhost:3000

# E-mail (Brevo)
BREVO_API_KEY=sua_chave_api_brevo
ALERT_SENDER_EMAIL=admin@aqualink.com
ALERT_SENDER_NAME=Aqualink Admin
```

## Instalação e Execução

1.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Execute a aplicação:**

    Utilizando uvicorn (servidor ASGI):

    ```bash
    uvicorn main:app --reload
    ```

    A API estará disponível em `http://localhost:8000`.

## Documentação da API

A documentação interativa (Swagger UI) é gerada automaticamente pelo FastAPI e pode ser acessada em:

*   **Swagger UI:** `http://localhost:8000/docs`
*   **ReDoc:** `http://localhost:8000/redoc`

### Principais Endpoints

#### Autenticação (`/auth`)
*   `POST /auth/login`: Realiza login e retorna token de acesso.
*   `POST /auth/invite`: Envia convite por e-mail (apenas Admin).
*   `POST /auth/register-invite`: Cria conta a partir de um convite.
*   `GET /auth/users`: Lista usuários (apenas Admin).

#### Dashboard (`/dashboard`)
*   `GET /dashboard/`: Retorna KPIs e dados consolidados para o painel de controle.

#### Relatórios (`/reports`)
*   `GET /reports/excel`: Baixa relatório Excel de períodos e KPIs escolhidos.
*   `GET /reports/excel-range`: Baixa relatório Excel personalizado por intervalo de datas e KPIs.

## Tecnologias Utilizadas

*   **Python 3.10+**
*   **FastAPI**: Framework web moderno e rápido.
*   **SQLAlchemy**: ORM e toolkit SQL.
*   **Pydantic**: Validação de dados.
*   **Pandas**: Manipulação de dados e geração de Excel.
*   **XlsxWriter**: Engine para criação de arquivos Excel.
*   **Passlib**: Hashing seguro de senhas.
*   **Brevo (Sendinblue)**: Serviço de envio de e-mails transacionais.
