#!/usr/bin/env bash
#
# deploy.sh — deploy do Aqualink na EC2: git pull + rebuild + up.
#
# Uso (rode a partir da raiz do repo, ~/eta-app):
#   ./deploy.sh                 # pull + rebuild de TODOS os serviços + up
#   ./deploy.sh frontend        # pull + rebuild só do frontend + up   (ex.: trocar logo/visual)
#   ./deploy.sh api             # pull + rebuild só da api + up         (ex.: lógica de backend)
#   ./deploy.sh api worker      # rebuild de api e worker
#   ./deploy.sh api --migrate   # idem + aplica migrações (`alembic upgrade head`)
#
# Notas:
#   - NÃO toca em segredos/.env (esses ficam só no servidor).
#   - Só mudou o .env? Não precisa rebuild: rode `docker compose up -d` (ou restart).
#   - --migrate só é necessário quando há uma NOVA revisão Alembic.
set -euo pipefail

# Vai para a pasta do script (raiz do repo), independente de onde foi chamado.
cd "$(dirname "$0")"

MIGRATE=0
SERVICES=()
for arg in "$@"; do
  if [ "$arg" = "--migrate" ]; then
    MIGRATE=1
  else
    SERVICES+=("$arg")
  fi
done

echo "==> git pull origin main"
git pull origin main

cd eta-stack

if [ "${#SERVICES[@]}" -eq 0 ]; then
  echo "==> docker compose build (todos os serviços)"
  docker compose build
else
  echo "==> docker compose build ${SERVICES[*]}"
  docker compose build "${SERVICES[@]}"
fi

echo "==> docker compose up -d"
docker compose up -d

if [ "$MIGRATE" -eq 1 ]; then
  echo "==> alembic upgrade head"
  docker compose exec -T api alembic upgrade head
  docker compose exec -T api alembic current
fi

echo "==> status:"
docker compose ps
echo "==> deploy concluído."
