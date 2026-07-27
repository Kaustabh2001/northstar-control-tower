FROM node:22-alpine AS build

WORKDIR /app
COPY apps/portal-web/package.json apps/portal-web/package-lock.json ./
RUN npm ci
COPY apps/portal-web ./
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM nginx:1.27-alpine
COPY apps/portal-web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
