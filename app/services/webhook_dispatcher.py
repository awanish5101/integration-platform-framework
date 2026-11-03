"""
Zero KTLO Webhook Dispatcher with Exponential Backoff Retries and Dead-Letter Queue (DLQ).
"""
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx
import logging

from app.models.webhook import WebhookEvent, WebhookStatus
from app.storage.repository import repo
from app.config import settings

logger = logging.getLogger("webhook_dispatcher")


class WebhookDispatcher:
    def __init__(self, repository=repo):
        self.repo = repository

    async def enqueue_and_dispatch(
        self,
        tenant_id: str,
        topic: str,
        payload: Dict[str, Any],
        target_url: str,
        max_attempts: int = settings.WEBHOOK_MAX_RETRIES
    ) -> WebhookEvent:
        event = WebhookEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            topic=topic,
            payload=payload,
            target_url=target_url,
            status=WebhookStatus.PENDING,
            attempts=0,
            max_attempts=max_attempts
        )
        self.repo.record_webhook(event)
        
        # Dispatch immediately
        return await self.dispatch_event(event)

    async def dispatch_event(self, event: WebhookEvent) -> WebhookEvent:
        """
        Executes HTTP dispatch with backoff retries. If attempts exceed max_attempts, moves to DLQ.
        """
        async with httpx.AsyncClient(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
            while event.attempts < event.max_attempts:
                event.attempts += 1
                try:
                    # In test environments or mock URLs
                    if event.target_url.startswith("mock://fail"):
                        raise httpx.RequestError("Target endpoint connection refused.")
                    elif event.target_url.startswith("mock://success"):
                        event.status = WebhookStatus.DELIVERED
                        event.last_status_code = 200
                        event.delivered_at = datetime.utcnow()
                        self.repo.record_webhook(event)
                        return event

                    response = await client.post(
                        event.target_url,
                        json={
                            "event_id": event.event_id,
                            "topic": event.topic,
                            "timestamp": event.created_at.isoformat(),
                            "data": event.payload
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    event.last_status_code = response.status_code
                    
                    if 200 <= response.status_code < 300:
                        event.status = WebhookStatus.DELIVERED
                        event.delivered_at = datetime.utcnow()
                        self.repo.record_webhook(event)
                        logger.info(f"Webhook {event.event_id} delivered successfully to {event.target_url}")
                        return event
                    else:
                        event.last_error = f"HTTP {response.status_code}: {response.text[:100]}"
                except Exception as e:
                    event.last_error = str(e)
                
                # Check if retries remaining
                if event.attempts < event.max_attempts:
                    event.status = WebhookStatus.RETRYING
                    backoff = settings.WEBHOOK_BACKOFF_BASE_SECONDS * (2 ** (event.attempts - 1))
                    await asyncio.sleep(backoff)

        # Max retries exceeded -> Escalate to Dead Letter Queue (Zero KTLO)
        event.status = WebhookStatus.FAILED_DLQ
        self.repo.record_webhook(event)
        logger.warning(f"Webhook {event.event_id} exhausted retries. Moved to DLQ: {event.last_error}")
        return event

    async def replay_dlq(self, event_ids: List[str]) -> List[WebhookEvent]:
        replayed = []
        for eid in event_ids:
            event = self.repo.get_webhook(eid)
            if event and event.status == WebhookStatus.FAILED_DLQ:
                # Reset attempt counter and dispatch
                event.attempts = 0
                event.status = WebhookStatus.PENDING
                result = await self.dispatch_event(event)
                replayed.append(result)
        return replayed


webhook_dispatcher = WebhookDispatcher()
