FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy code and schema
COPY tsconfig.json next.config.ts postcss.config.mjs eslint.config.mjs ./
COPY prisma ./prisma
COPY public ./public
COPY src ./src

# Generate Prisma Client
RUN npx prisma generate --schema=prisma/schema.prisma

# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED 1
ENV DATABASE_URL "file:/app/shared/dev.db"

# Build the Next.js application
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy package info
COPY package*.json ./

# Copy build artifacts, complete node_modules and Prisma schema from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/prisma ./prisma

# Standard environment settings
ENV NODE_ENV production
ENV PORT 3000
ENV NEXT_TELEMETRY_DISABLED 1

EXPOSE 3000

# Start using the Next.js binary directly
CMD ["npx", "next", "start", "-p", "3000"]
