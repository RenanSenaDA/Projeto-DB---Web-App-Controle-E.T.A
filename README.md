# 🌊 Projeto Webapp - E.T.A

## 📌 Visão Geral

O **Projeto Webapp - E.T.A** tem como objetivo criar uma solução integrada para **monitoramento em tempo real de Estações de Tratamento de Água (ETA)**, conectando sensores industriais a um sistema centralizado de visualização e análise.  

O projeto busca transformar dados brutos coletados por PLCs em **informações acionáveis**, permitindo acompanhamento de indicadores de qualidade, desempenho dos equipamentos e geração de relatórios de eficiência.

---

## 🎯 Problema a Resolver

Nas operações de tratamento de água, os dados de campo muitas vezes ficam **fragmentados**, sendo acessados apenas localmente em cada equipamento ou exportados manualmente em planilhas. Isso gera:

- Dificuldade de **visualização em tempo real** da planta como um todo  
- **Perda de histórico** de dados e dificuldade em identificar tendências  
- **Dependência de registros manuais**, sujeitos a falhas  
- Pouco suporte a análises preditivas e relatórios automatizados  

O projeto propõe um **sistema centralizado**, capaz de integrar medições de diferentes fontes e disponibilizar relatórios e dashboards em tempo real, reduzindo riscos e aumentando a eficiência operacional.

---

## 🚀 Objetivos

- Integrar dados de **sensores/CLPs** com banco de dados centralizado
- Disponibilizar dashboards interativos para acompanhamento de KPIs
- Automatizar relatórios de desempenho e qualidade da água
- Permitir análise de alarmes e eventos de forma preditiva
- Criar uma base sólida para futuras integrações em nuvem

---

## 🛠️ Tecnologias Utilizadas

### Banco de Dados
- **PostgreSQL**  
  Banco relacional para armazenar medições de forma estruturada (`sensor` e `measurement`).

- **Docker Compose**  
  Orquestração dos serviços (Postgres, Streamlit, Node-RED, pgAdmin), simplificando deploy e ambiente.

### Ingestão de Dados
- **Node-RED**  
  Faz a integração direta com o **PLC** (via drivers/ protocolos industriais) e envia as medições para o PostgreSQL.  
  > Hoje é o **caminho principal de ingestão**, substituindo a etapa anterior de simulação por buffer.

- **(Sugestão futura) MQTT / Mosquitto**  
  Embora não esteja em uso atualmente, o MQTT pode ser útil para integrar sensores IoT, gateways ou replicar dados para outros sistemas.


### Visualização
- **Streamlit**  
  Framework Python para dashboards interativos em tempo real.  
- **Grafana (opcional)**  
  Pode ser conectado ao Postgres para análises avançadas e dashboards adicionais.

### Ferramentas de Apoio
- **pgAdmin** → administração e consultas no Postgres  
- **GitHub** → versionamento, documentação e colaboração  

---

## 🧩 Componentes Criados

- `api/` (FastAPI)
  - Endpoints para dashboard, séries temporais, limites, alarmes e relatórios.
  - Iniciar: `pip install -r api/requirements.txt` e `uvicorn main:app --reload --port 8000` (dentro de `api/`).
  - Variáveis: `DATABASE_URL` (ou `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`), `LOCAL_TZ`, `FEED_INTERVAL`.
  - Endpoints:
    - `GET /dashboard`
    - `GET /measurements/latest`
    - `GET /measurements/series?tags=...&minutes=...`
    - `GET /limits` e `PUT /limits`
    - `GET /alarms/status` e `PUT /alarms/status`
    - `GET /reports/excel`
    - `POST /auth/login` e `POST /auth/register`

- `frontend/` (Next.js)
  - Interface web com Dashboard, Séries Temporais, Relatórios e Configurações.
  - Iniciar: `npm install` e `npm run dev` (dentro de `frontend/`).
  - Variáveis: `NEXT_PUBLIC_API_BASE_URL` (padrão `http://localhost:8000`).
  - Observação: Dashboard atualiza a cada 60s; Séries Temporais atualizam ao mudar filtros/intervalo.

- `eta-stack/`
  - `docker-compose.yml` orquestra `streamlit/` e `worker/`.
  - Iniciar: `docker compose up -d` (dentro de `eta-stack/`).
  - Requer `.env` em `streamlit/` (referenciado no compose).

- `streamlit/`
  - App Streamlit (opcional) para visualização rápida.
  - Iniciar: `pip install -r streamlit/requirements.txt` e `python -m streamlit run streamlit/streamlit_eta_app.py` (porta `8501`).

- `worker/`
  - Serviços de alarmes e ingestões (`alarm_worker.py`, `feeder_loop.py`).
  - Iniciar: `pip install -r worker/requirements.txt` e executar o script desejado (`python alarm_worker.py`).


## 📊 O que o sistema faz hoje

- Captura de dados em tempo real a partir de sensores ou simulações
- Armazenamento estruturado no banco PostgreSQL
- Dashboards interativos via Streamlit
- Possibilidade de relatórios periódicos (diários, semanais, mensais)
- Estrutura preparada para:
  - **Alarmes e eventos** (limiares configuráveis)
  - **KPIs de operação**: turbidez, TMP, recovery, rejeição, consumo de energia, vazão
  - **Análises preditivas** futuras (ex.: fouling, degradação de membranas)
  - **Autenticação de Usuário** para administradores

---

## 🌟 Benefícios Esperados

- **Centralização** das informações operacionais
- **Redução de falhas humanas** (menos registros manuais)
- **Acompanhamento remoto em tempo real**
- **Decisões baseadas em dados** (histórico consolidado e dashboards)
- Base para **expansão em nuvem** e integração com sistemas de BI ou CMMS

---

## 📌 Status do Projeto

- Versão inicial com ingestão de dados **via buffer** em Python + Streamlit  
- Versão evoluída com ingestão de dados de **PLC → Node-RED → PostgreSQL**  
- Estrutura preparada para **migração futura para nuvem (Cloudflare / Edge IoT)**  

---

## 📅 Próximos Passos

1. Integração em campo: conectar a uma ETA real (PLC/CLP via Modbus/TCP ou OPC UA), mapear tags, calibrar unidades e validar KPIs com equipe de processo.

2. Subir para a nuvem (AWS):

3. Escalabilidade & custos: particionamento/TimescaleDB, retenção/arquivamento em S3 (Glue/Athena), backup e DR (RPO/RTO).

4. Multi-site: suporte a múltiplas ETAs (tabela site, segregação por tenant) e perfis por planta.

5. UX: dashboards por perfil (operador, manutenção, gestor) e relatórios agendados (PDF/Excel).

---

✍️ **Projeto em desenvolvimento colaborativo**: feedbacks e contribuições são bem-vindos.



## 📌 Como Funciona?
---

# 🌐 Cenário

- **Máquina A**
  - Conectada ao **PLC**
  - Tem o **Node-RED** rodando (`http://192.xxx.x.xx:xxxx`)
  - Função: ler os dados do PLC e inserir no Postgres

- **Máquina B**
  - Roda o **PostgreSQL em Docker** (porta `5432` exposta)
  - Contém o banco **eta** com tabelas `sensor` e `measurement`
  - Função: receber conexões externas e armazenar os dados

---

# ✅ Passo a passo

## 1) Na **Máquina B** (Postgres)

### a) Descobrir o IP interno
No terminal/PowerShell:
   powershell
ipconfig

b) Garantir que o container Postgres está expondo a porta:
docker ps

c) Liberar porta no firewall

Abra PowerShell como administrador:
New-NetFirewallRule -DisplayName "Postgres 5432 (LAN)" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow -Profile Any

d) Confirmar que a porta está acessível

Na Máquina A, rode:

Test-NetConnection -ComputerName 192.xxx.x.xx -Port 5432

Se TcpTestSucceeded = True, está pronto para conectar.


2) Na Máquina A (Node-RED + PLC)
a) Acessar Node-RED

Abra no navegador da Máquina A ou da Máquina B:

http://192.xxx.x.xx:xxxx

b) Instalar o nó Postgres no Node-RED

Menu → Manage palette → Install → procurar node-red-contrib-postgres.

c) Configurar servidor Postgres no nó:
Host: 192.xxx.x.xx:xxxx (IP da Máquina B)

Port: 5432

Database: eta

User: postgres (ou conforme .env)

Password: postgres (ou conforme .env)

SSL: desmarcado (na LAN não precisa)

3) Fluxo de dados completo
PLC → Node-RED (Máquina A) → Rede Local (192.xxx.x.xx) → PostgreSQL em Docker (Máquina B)


O Node-RED não precisa do banco local, só do IP da Máquina B

O Postgres precisa estar com firewall liberado e escutando na porta 5432

4) Teste rápido

No Node-RED, crie um inject com:

topic = "pH"

payload = 7.1

Dispare → se tudo certo, veja no debug e confirme no pgAdmin (Máquina B):

SELECT m.ts, s.tag, m.value
FROM eta.measurement m
JOIN eta.sensor s ON s.id = m.sensor_id
ORDER BY m.ts DESC
LIMIT 10;

5) Inicialização do Streamlit

Na Máquina B (ou onde roda o webapp), com a venv ativada:

.\.venv\Scripts\python -m streamlit run .\streamlit\streamlit_eta_app.py


O app ficará disponível em:

http://localhost:8501


🏷️ Versões

v1.0-fase1 — autenticação + alertas por limiar + ingestão Node-RED + dashboards + relatórios básicos.

---

## ✅ Informações complementares e pendências

- Criar `.env` em `streamlit/` para uso pelo `eta-stack/docker-compose.yml`.
- Configurar `NEXT_PUBLIC_API_BASE_URL` no `frontend` apontando para a API (padrão `http://localhost:8000`).
- Configurar `DATABASE_URL` (ou `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`) na `api` para conexão ao Postgres.
- Mapear e documentar os nomes de tags dos sensores (ex.: `bombeamento/vazao`, `qualidade/ph`) para facilitar filtros na UI.
- Fluxos do Node-RED não estão versionados aqui; garantir que a ingestão está ativa (Máquina A → Postgres).

---

## ▶️ Subir localmente (API + Frontend)

1) API (PowerShell)

```
cd api
python -m venv .venv
\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
${env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/eta"}
uvicorn main:app --reload --port 8000
```

2) Frontend (PowerShell)

```
cd frontend
npm install
${env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"}
npm run dev
```

Observação:
- A API sobe em `http://localhost:8000` e o Frontend em `http://localhost:3000`.
- Se `NEXT_PUBLIC_API_BASE_URL` não for definido, o frontend usa `http://localhost:8000` por padrão.

