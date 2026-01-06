# =============================================================================
# Dockerfile pour WIDIP MCP Server
# Serveur MCP (Model Context Protocol) Python pour WIDIP
# =============================================================================

FROM python:3.11-slim as builder

# Variables de build
ARG POETRY_VERSION=1.8.2

# Installer poetry
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Copier les fichiers de dépendances
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Installer les dépendances (sans dev) dans un venv
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --only=main --no-interaction --no-ansi

# =============================================================================
# Image de production
# =============================================================================

FROM python:3.11-slim as runtime

# Labels
LABEL org.opencontainers.image.title="WIDIP MCP Server"
LABEL org.opencontainers.image.description="Serveur MCP Python pour intégrations WIDIP"
LABEL org.opencontainers.image.vendor="WIDIP"
LABEL org.opencontainers.image.version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Path du virtualenv
    PATH="/app/.venv/bin:$PATH"

# Créer un utilisateur non-root
RUN groupadd --gid 1000 widip && \
    useradd --uid 1000 --gid widip --shell /bin/bash --create-home widip

# Dossier de travail
WORKDIR /app

# Copier le virtualenv depuis le builder
COPY --from=builder /app/.venv /app/.venv

# Copier le code source
COPY --chown=widip:widip src/ /app/src/

# Passer à l'utilisateur non-root
USER widip

# Exposer le port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:3001/health')" || exit 1

# Commande par défaut
CMD ["python", "-m", "src.main"]
