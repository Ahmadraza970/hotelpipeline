FROM python:3.11-slim

# System Python linters that ruff (pip) depends on are bundled. We also install
# Node so the optional eslint/tsc backends can run if present.
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Optionally install Node for JS/TS linting (best-effort; backends degrade
# gracefully and fall back to the LLM judge if absent).
ARG INSTALL_NODE=true
RUN if [ "$INSTALL_NODE" = "true" ]; then \
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
        && apt-get install -y --no-install-recommends nodejs \
        && npm install -g eslint typescript typescript-eslint globals \
        && rm -rf /root/.npm /tmp/npm-* ; \
    fi

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Create a non-root user.
RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser/app

COPY --chown=appuser:appuser backend ./backend
ENV PYTHONPATH=/home/appuser/app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
