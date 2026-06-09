# Migrações de banco (Alembic)

A partir de agora **o schema do banco é versionado com Alembic**. Nunca crie ou
altere tabelas manualmente em produção — toda mudança de schema vira uma revisão
aqui em `migrations/versions/`.

A URL de conexão vem da configuração da aplicação (`DATABASE_URL` ou as
variáveis `PG*` do `.env`), via `database/connection.py` — não há credenciais no
`alembic.ini`. Rode os comandos a partir da pasta `api/` (ou de `/app` no
container).

## Aplicar as migrações

```bash
cd api                      # ou /app dentro do container
alembic upgrade head
```

A baseline (`0001_baseline_schema`) é **idempotente** (`CREATE ... IF NOT EXISTS`),
então `alembic upgrade head` é seguro nos dois cenários:

- **Banco novo** (local/dev): cria todo o schema `eta` do zero.
- **Banco atual de produção** (RDS, que já tem as tabelas): vira no-op no que já
  existe e apenas registra a versão em `alembic_version`.

> Alternativa para o banco já existente: `alembic stamp head` apenas marca a
> versão sem rodar DDL. Como a baseline é idempotente, `upgrade head` também
> serve e é o comando padrão.

## Ver estado / histórico

```bash
alembic current      # revisão aplicada no banco
alembic history      # todas as revisões
alembic heads        # topo(s) da árvore
```

## Gerar o SQL sem aplicar (revisão/auditoria)

```bash
alembic upgrade head --sql > schema.sql   # modo offline, não conecta ao banco
```

## Criar uma nova migração

O projeto usa SQL parametrizado (sem ORM), então as revisões são **escritas à
mão** (não use `--autogenerate`):

```bash
alembic revision -m "descricao curta da mudanca"
```

Edite o arquivo gerado em `versions/` e preencha `upgrade()` / `downgrade()` com
`op.execute("... SQL ...")`. Prefira DDL reversível e teste antes de aplicar em
produção.

> **Sempre qualifique os objetos com o schema `eta`** (ex.: `eta.measurement`,
> não apenas `measurement`). O `SET search_path` da baseline vale só para aquela
> revisão; ele não persiste para as revisões seguintes, então não dependa dele.

## Deploy (fluxo do projeto)

Editar localmente → commit → push → na EC2 `git pull` → rebuild do container da
API (o `alembic` está no `requirements.txt`) → rodar `alembic upgrade head` no
container:

```bash
docker compose exec api alembic upgrade head
```
