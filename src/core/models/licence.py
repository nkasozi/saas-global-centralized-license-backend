from datetime import datetime
from enum import Enum

from src.core.models.model import Model


class LicenseStatus(Enum):
    VALID = "valid"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class License (Model):
    id: int
    product_id: int
    status: LicenseStatus
    expires_at: datetime
    created_at: datetime
    max_seats_override: int

    def is_active(self)-> bool:
        return self.status == LicenseStatus.VALID and self.expires_at > datetime.now()