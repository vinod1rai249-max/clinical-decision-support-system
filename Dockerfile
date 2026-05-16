# Use full python image for guaranteed system dependencies
FROM python:3.12

WORKDIR /app

# System configuration
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app
ENV HF_HOME=/app/model_cache

# Install UV for reliable dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the project and dependencies
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache .

# Pre-download the model into the container
RUN mkdir -p /app/model_cache && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/model_cache')"

# Copy the rest of the code
COPY . .

# Fix permissions
RUN chmod -R 777 /app/model_cache

EXPOSE 8080

# START COMMAND - Use standard port binding
CMD uvicorn api:app --host 0.0.0.0 --port 8080 --workers 1
