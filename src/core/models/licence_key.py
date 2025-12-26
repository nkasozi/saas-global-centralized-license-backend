import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from result import Err, Ok, Result

from src.core.models.model import Model


@dataclass
class LicenseKey(Model):
    brand_id: str = ""
    end_product_user_id: str = ""
    key_string: str = ""
    license_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(brand_id: str, end_product_user_id: str) -> Result["LicenseKey", str]:
        if not brand_id or not brand_id.strip():
            return Err("Brand ID cannot be empty")
        if not end_product_user_id or not end_product_user_id.strip():
            return Err("End product user ID cannot be empty")

        generated_key = LicenseKey._generate_key_string()
        return Ok(
            LicenseKey(
                id=str(uuid4()),
                brand_id=brand_id,
                end_product_user_id=end_product_user_id,
                key_string=generated_key,
                license_ids=[],
                created_at=datetime.now(timezone.utc),
            )
        )

    @staticmethod
    def _generate_key_string() -> str:
        return secrets.token_hex(16)
