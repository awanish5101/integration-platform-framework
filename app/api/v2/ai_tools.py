"""
AI-driven Tooling and Zero-KTLO Webhook Management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from app.services.ai_connector_service import (
    ai_connector_service,
    SchemaAnalysisResult,
    SchemaDriftReport
)
from app.services.webhook_dispatcher import webhook_dispatcher
from app.models.webhook import WebhookEvent, DLQReplayRequest
from app.storage.repository import repo
from app.core.security import get_current_tenant

router = APIRouter(prefix="/tools", tags=["AI Tooling & Zero-KTLO Automation"])


@router.post("/synthesize-connector", response_model=SchemaAnalysisResult)
def synthesize_connector(
    payload: Dict[str, Any],
    entity_name: str = "employee"
):
    """
    AI-driven Tooling: Ingests an arbitrary third-party JSON payload or schema
    and automatically infers field mappings to standardized HRIS structures.
    """
    return ai_connector_service.synthesize_connector_mapping(payload, entity_name)


@router.post("/detect-schema-drift", response_model=SchemaDriftReport)
def detect_drift(request: Dict[str, Any]):
    """
    Zero-KTLO resilience check: Validates live API payloads against registered JSON schemas
    to alert developers of upstream breaking changes.
    """
    expected = request.get("expected_schema", {})
    observed = request.get("observed_payload", {})
    return ai_connector_service.detect_schema_drift(expected, observed)


@router.post("/generate-stub")
def generate_stub(app_slug: str, analysis: SchemaAnalysisResult) -> Dict[str, str]:
    """Generates an executable Python connector adapter from synthesized schema mappings."""
    code = ai_connector_service.generate_connector_stub(app_slug, analysis.mappings)
    return {"generated_code": code}


# --- Zero-KTLO Webhook & DLQ routes ---
@router.post("/webhooks/dispatch", response_model=WebhookEvent)
async def dispatch_webhook(
    topic: str,
    target_url: str,
    payload: Dict[str, Any],
    tenant_id: str = Depends(get_current_tenant)
):
    """Dispatches an event to an external third-party webhook endpoint with automated retries."""
    return await webhook_dispatcher.enqueue_and_dispatch(tenant_id, topic, payload, target_url)


@router.get("/webhooks/dlq", response_model=List[WebhookEvent])
def get_dead_letter_queue(tenant_id: str = Depends(get_current_tenant)):
    """Zero-KTLO observability: Inspects all poisoned/failed events quarantined in the DLQ."""
    return repo.list_dlq_events(tenant_id)


@router.post("/webhooks/dlq/replay", response_model=List[WebhookEvent])
async def replay_dlq_events(
    request: DLQReplayRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    """Replays quarantined dead-letter events after upstream third-party service recovery."""
    return await webhook_dispatcher.replay_dlq(request.event_ids)
