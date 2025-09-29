# 🌊 Projeto Webapp - E.T.A

Integração de dados de um **PLC** através do **Node-RED** com um **banco PostgreSQL em Docker**, disponibilizando visualização e relatórios via **Streamlit**.

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


Se usar Docker Compose:

docker-compose up app

