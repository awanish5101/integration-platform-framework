"""
Webhook and Dead-Letter Queue (DLQ) event models for Zero KTLO automation.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class WebhookStatus(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    RETRYING = "RETRYING"
    FAILED_DLQ = "FAILED_DLQ"


class WebhookEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    tenant_id: str = Field(..., description="Tenant producing or receiving event")
    topic: str = Field(..., description="Event topic, e.g. 'employee.onboarded', 'app.installed'")
    payload: Dict[str, Any] = Field(..., description="Normalized JSON payload")
    target_url: str = Field(..., description="Destination third-party webhook URL")
    status: WebhookStatus = Field(default=WebhookStatus.PENDING)
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)
    last_error: Optional[str] = None
    last_status_code: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None


class DLQReplayRequest(BaseModel):
    event_ids: list[str] = Field(..., description="List of dead-lettered event IDs to re-dispatch")
