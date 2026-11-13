# Use Python 3.11
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client library
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies with optional postgres support
ARG INSTALL_SPEC=.
RUN pip install --no-cache-dir "$INSTALL_SPEC"

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create entrypoint script
RUN echo '#!/bin/sh\nset -e\nalembic upgrade head\nexec "$@"' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Create data directory and set permissions
RUN mkdir -p /data && chmod 777 /data

EXPOSE 9000

ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
