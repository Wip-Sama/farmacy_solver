# Stage 1: Build Frontend SPA
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend & ASP Solver Runtime
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system dependencies (build tools, fonts, C libraries for Clingo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    fontconfig \
    fonts-dejavu \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python codebase and configs
COPY backend/ ./backend/
COPY core/ ./core/
COPY data/ ./data/
COPY app_config.yaml .

# Copy compiled frontend from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose server port
EXPOSE 8001

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/api/settings || exit 1

# Start FastAPI application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
