"""Validated schema for the gateway configuration file."""

from pydantic import BaseModel, ConfigDict, Field


class SensorConfig(BaseModel):
    """A simulated sensor attached to the gateway."""

    model_config = ConfigDict(strict=True)

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    unit: str = Field(min_length=1)


class GatewayConfig(BaseModel):
    """Required gateway settings."""

    model_config = ConfigDict(strict=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    location: str = Field(min_length=1)
    sensors: list[SensorConfig] = Field(min_length=1)
    reporting_interval_seconds: int = Field(gt=0)


class GatewayConfigDocument(BaseModel):
    """Top-level structure of ``gateway.yaml``."""

    model_config = ConfigDict(strict=True)

    gateway: GatewayConfig
