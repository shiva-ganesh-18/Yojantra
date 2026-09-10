# Yojantra frontend — PRODUCTION image.
# Compiled Vite bundle served by nginx. Local development uses Dockerfile.dev
# (via docker-compose.override.yml) with the Vite dev server instead.
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# Vite bakes VITE_* values in at build time; all default to empty (except the
# API URL) so the image builds without secrets. Supply real values as build
# args in production.
ARG VITE_API_URL=http://127.0.0.1:8001
ARG VITE_FIREBASE_API_KEY=
ARG VITE_FIREBASE_AUTH_DOMAIN=
ARG VITE_FIREBASE_PROJECT_ID=
ARG VITE_FIREBASE_STORAGE_BUCKET=
ARG VITE_FIREBASE_MESSAGING_SENDER_ID=
ARG VITE_FIREBASE_APP_ID=

RUN npm run build

FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
