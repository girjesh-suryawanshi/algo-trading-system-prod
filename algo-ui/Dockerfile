FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm config set fetch-retry-maxtimeout 120000 && \
    npm config set fetch-retries 5 && \
    npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist/algo-ui /usr/share/nginx/html
EXPOSE 80
