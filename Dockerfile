
FROM python:3.14-slim

WORKDIR /project

# Configure Python to run cleanly inside Docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/project

# Install application dependencies.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and scraper source configuration.
COPY app ./app
COPY sources.yaml ./sources.yaml

EXPOSE 8003

# Start the Orion API by default.
# The worker overrides this command in compose.yaml.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
