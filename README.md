# Orion

![Orion project banner](orion-banner.png)

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-8-FF4438?logo=redis&logoColor=white)](https://redis.io/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

Orion collects job vacancies from public sources and provides them through a REST API. A background worker updates the data on a schedule.

## Architecture

![Orion architecture diagram](diagramm.png)

## Run with Docker

You need Docker and Docker Compose.

1. Create a local environment file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and set `POSTGRES_PASSWORD`, `SCRAPE_API_KEY`, and `JWT_SECRET_KEY` to your own values.

3. Create the Docker network and start the services:

   ```bash
   docker network create back_end
   docker compose up --build -d
   ```

The API is available at <http://localhost:8003>. Open <http://localhost:8003/docs> for the interactive API documentation. Check its status at <http://localhost:8003/health>.

## Stop

```bash
docker compose down
```
