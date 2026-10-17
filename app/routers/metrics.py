# ==============================
# Standard library imports
# ==============================

import asyncio
import logging

# ==============================
# Third-party imports
# ==============================

import jwt
import psutil

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

# ==============================
# Application imports
# ==============================

from app.routers.dependencies import jwt_manager
from app.schemas import SystemMetricsRead


# ==============================
# Logger configuration
# ==============================

logger = logging.getLogger(__name__)


# ==============================
# Metrics router
# ==============================

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
)


# ==============================
# Server metrics WebSocket
# ==============================

@router.websocket("/ws/stats")
async def metrics_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """Stream process metrics to authenticated administrators."""
    # Require an access token.
    if not token:
        await websocket.close(code=1008)
        return

    # Validate the token before accepting the connection.
    try:
        payload = jwt_manager.validate_access_token(token)

    except jwt.InvalidTokenError:
        await websocket.close(code=1008)
        return

    # Allow administrators only.
    roles = payload.get("roles", [])

    if not isinstance(roles, list) or "admin" not in roles:
        await websocket.close(code=1008)
        return

    # Accept the connection after successful authentication.
    await websocket.accept()
    logger.info("Administrator connected to the metrics WebSocket.")

    # Monitor the current API process.
    process = psutil.Process()

    # Initialize CPU measurement before collecting the first sample.
    process.cpu_percent()

    try:
        while True:
            # Sample metrics once per second.
            await asyncio.sleep(1)

            memory = process.memory_info()

            metrics = SystemMetricsRead(
                cpu_percent=round(process.cpu_percent(), 2),
                memory_percent=round(process.memory_percent(), 2),
                memory_used_mb=round(memory.rss / (1024 ** 2)),
            )

            # Send a validated JSON payload to the client.
            await websocket.send_json(metrics.model_dump())

    except WebSocketDisconnect:
        logger.info("Administrator disconnected from the metrics WebSocket.")
