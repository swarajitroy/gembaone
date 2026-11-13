# Build stage
FROM node:22 AS build

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source and shared config
COPY frontend/ ./
COPY shared_config.json /app/shared_config.json

# Build the application
RUN npm run build

# Runtime stage with nginx
FROM nginx:alpine

# Backend host can be overridden via build arg
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}

# Copy nginx template
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy built assets
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
