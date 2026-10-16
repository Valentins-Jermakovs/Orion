FROM python:3.12-slim

# Python runtime settings.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Create a non-root user for the application.
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app

# Install Python dependencies first for better layer caching.
COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Copy application source code and scraper configuration.
COPY --chown=app:app app/ ./app/
COPY --chown=app:app sources.yaml ./sources.yaml

# Run the application without root privileges.
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]