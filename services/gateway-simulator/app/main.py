"""FastAPI application for the simulated IoT gateway."""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from .config import config_is_valid

app = FastAPI(title="NexGuard Gateway Simulator", version="0.1.0")

CONFIG_VALID = Gauge(
    "gateway_simulator_config_valid",
    "Whether the gateway simulator configuration passed validation.",
)


@app.get("/health", response_class=JSONResponse)
def health() -> JSONResponse:
    """Report health based on the latest configuration contents."""

    if config_is_valid():
        CONFIG_VALID.set(1)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "healthy"},
        )

    CONFIG_VALID.set(0)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unhealthy", "reason": "config_invalid"},
    )


@app.get("/metrics", response_class=Response)
def metrics() -> Response:
    """Expose metrics in Prometheus text format."""

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
