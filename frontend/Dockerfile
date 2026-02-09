# ---------- deps ----------
FROM node:20.11.1-alpine AS deps
WORKDIR /app

# Copia manifests de dependências
COPY package.json package-lock.json ./

# Instala dependências de forma reprodutível e bloqueando scripts (proteção)
RUN npm ci --ignore-scripts


# ---------- build ----------
FROM node:20.11.1-alpine AS build
WORKDIR /app

# Reaproveita node_modules do estágio deps
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json
COPY --from=deps /app/package-lock.json ./package-lock.json

# Copia o restante do código
COPY . .

# Build do Next
RUN npm run build


# ---------- runner ----------
FROM node:20.11.1-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copia artefatos necessários do build
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/package-lock.json ./package-lock.json
COPY --from=build /app/public ./public
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "run", "start"]
