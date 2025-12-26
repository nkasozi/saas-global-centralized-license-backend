from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from result import Err, Ok, Result


class WebhookEvent(str, Enum):
    LICENSE_PROVISIONED = "license.provisioned"
    LICENSE_ACTIVATED = "license.activated"
    LICENSE_DEACTIVATED = "license.deactivated"
    LICENSE_SUSPENDED = "license.suspended"
    LICENSE_RESUMED = "license.resumed"
    LICENSE_RENEWED = "license.renewed"
    LICENSE_CANCELLED = "license.cancelled"


class WebhookStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"


@dataclass
class Webhook:
    id: str = ""
    brand_id: str = ""
    url: str = ""
    events: list[WebhookEvent] = field(default_factory=list)
    secret: str = ""
    status: WebhookStatus = WebhookStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0
    max_failures: int = 5

    @staticmethod
    def create(
        brand_id: str,
        url: str,
        events: list[WebhookEvent],
        secret: str,
    ) -> Result["Webhook", str]:
        if not brand_id or not brand_id.strip():
            return Err("Brand ID cannot be empty")

        if not url:
            return Err("URL is required")

        if not url.startswith(("http://", "https://")):
            return Err("URL must start with http:// or https://")

        if not events:
            return Err("At least one event must be subscribed")

        if len(events) > len(WebhookEvent):
            return Err(f"Cannot subscribe to more than {len(WebhookEvent)} events")

        if not secret or len(secret) < 8:
            return Err("Secret must be at least 8 characters")

        webhook = Webhook(
            id=str(uuid4()),
            brand_id=brand_id,
            url=url,
            events=events,
            secret=secret,
            status=WebhookStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return Ok(webhook)

    def is_active(self) -> bool:
        return self.status == WebhookStatus.ACTIVE and self.failure_count < self.max_failures

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.status = WebhookStatus.FAILED

    def reset_failure_count(self) -> None:
        self.failure_count = 0
        self.status = WebhookStatus.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "url": self.url,
            "events": [e.value for e in self.events],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "failure_count": self.failure_count,
        }
