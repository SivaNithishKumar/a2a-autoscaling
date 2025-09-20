# Multi-stage build for Research Agent
FROM python:3.12-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files from current directory
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Install UV for fast dependency management
RUN pip install uv

# Install dependencies
RUN uv pip install --system -e .

# Production stage
FROM python:3.12-slim as production

# Create non-root user for security
RUN groupadd -r a2a && useradd -r -g a2a -s /bin/false a2a

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/

# Create logs directory
RUN mkdir -p /app/logs && chown -R a2a:a2a /app

# Switch to non-root user
USER a2a

# Expose ports
EXPOSE 8083

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8083/health || exit 1

# Environment variables
ENV PYTHONPATH=/app/src
ENV AGENT_PORT=8083
ENV AGENT_HOST=0.0.0.0
ENV LOG_LEVEL=INFO

# Run the agent
CMD ["python", "-m", "agents.research", "--host", "0.0.0.0", "--port", "8083"]
