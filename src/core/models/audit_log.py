from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from result import Err, Ok, Result


class AuditOperation(str, Enum):
    BRAND_CREATED = "BRAND_CREATED"
    BRAND_UPDATED = "BRAND_UPDATED"
    BRAND_DELETED = "BRAND_DELETED"

    PRODUCT_CREATED = "PRODUCT_CREATED"
    PRODUCT_UPDATED = "PRODUCT_UPDATED"
    PRODUCT_DELETED = "PRODUCT_DELETED"

    LICENSE_PROVISIONED = "LICENSE_PROVISIONED"
    LICENSE_ACTIVATED = "LICENSE_ACTIVATED"
    LICENSE_DEACTIVATED = "LICENSE_DEACTIVATED"
    LICENSE_SUSPENDED = "LICENSE_SUSPENDED"
    LICENSE_RESUMED = "LICENSE_RESUMED"
    LICENSE_RENEWED = "LICENSE_RENEWED"
    LICENSE_CANCELLED = "LICENSE_CANCELLED"

    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"

    AUTH_TOKEN_GENERATED = "AUTH_TOKEN_GENERATED"
    AUTH_TOKEN_REVOKED = "AUTH_TOKEN_REVOKED"
    AUTH_FAILED = "AUTH_FAILED"

    WEBHOOK_CREATED = "WEBHOOK_CREATED"
    WEBHOOK_TRIGGERED = "WEBHOOK_TRIGGERED"
    WEBHOOK_FAILED = "WEBHOOK_FAILED"


@dataclass
class AuditLog:
    id: str = ""
    brand_id: str = ""
    operation: AuditOperation = AuditOperation.BRAND_CREATED
    resource_type: str = ""
    resource_id: str = ""
    user_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    changes: dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "SUCCESS"
    error_message: Optional[str] = None

    @staticmethod
    def create(
        brand_id: str,
        operation: AuditOperation,
        resource_type: str,
        resource_id: str,
        changes: Optional[dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Result["AuditLog", str]:
        if not resource_type:
            return Err("Resource type is required")

        audit_log = AuditLog(
            id=str(uuid4()),
            brand_id=brand_id,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return Ok(audit_log)

    @staticmethod
    def create_failure(
        brand_id: str,
        operation: AuditOperation,
        error_message: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Result["AuditLog", str]:

        audit_log = AuditLog(
            brand_id=brand_id,
            operation=operation,
            resource_type="SYSTEM",
            resource_id="",
            status="FAILURE",
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return Ok(audit_log)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "operation": self.operation.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
        }
