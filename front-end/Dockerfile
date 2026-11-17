FROM node:24-bookworm-slim AS builder
WORKDIR /app
RUN npm install --global pnpm@12.6.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY packages ./packages
COPY apps ./apps
RUN pnpm install --frozen-lockfile
ARG APP_NAME
# This URL is used by the browser, so it must be reachable from the host.
ARG NEXT_PUBLIC_GATEWAY_URL=http://localhost:8080/api/v1
ENV NEXT_PUBLIC_GATEWAY_URL=$NEXT_PUBLIC_GATEWAY_URL NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter "${APP_NAME}" build && mkdir -p "apps/${APP_NAME}/public"

FROM node:24-bookworm-slim AS runner
WORKDIR /app
ARG APP_NAME
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
COPY --from=builder --chown=node:node /app/apps/${APP_NAME}/.next/standalone ./
COPY --from=builder --chown=node:node /app/apps/${APP_NAME}/.next/static ./apps/${APP_NAME}/.next/static
COPY --from=builder --chown=node:node /app/apps/${APP_NAME}/public ./apps/${APP_NAME}/public
WORKDIR /app/apps/${APP_NAME}
USER node
EXPOSE 3000
CMD ["node", "server.js"]
