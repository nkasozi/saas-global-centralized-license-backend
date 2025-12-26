from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from result import Err, Ok, Result

from src.core.models.model import Model


class LicenseStatus(Enum):
    VALID = "valid"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


@dataclass
class License(Model):
    product_id: str = ""
    status: LicenseStatus = LicenseStatus.VALID
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        return self.status == LicenseStatus.VALID and self.expires_at > datetime.now(timezone.utc)

    @staticmethod
    def create(product_id: str, expires_at: datetime) -> Result["License", str]:
        if not product_id or not product_id.strip():
            return Err("Product ID cannot be empty")
        if expires_at <= datetime.now(timezone.utc):
            return Err("Expiration date must be in the future")
        return Ok(
            License(
                id=str(uuid4()),
                product_id=product_id,
                status=LicenseStatus.VALID,
                expires_at=expires_at,
                created_at=datetime.now(timezone.utc),
            )
        )
