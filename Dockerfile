# USE FULL PYTHON IMAGE (Not Slim) for maximum system library compatibility
FROM python:3.12

WORKDIR /app

# System variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app
ENV HF_HOME=/app/model_cache

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies system-wide
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# Pre-bake the model weights into the container
RUN mkdir -p /app/model_cache && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/model_cache')"

# Copy ALL code
COPY . .

# Ensure standard port 8080
EXPOSE 8080

# START INSTANTLY - No blocking imports
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
