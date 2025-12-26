from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from result import Err, Ok, Result

from src.core.models.model import Model


@dataclass
class Brand(Model):
    brand_name: str = ""
    api_hash_key: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(brand_name: str) -> Result["Brand", str]:
        if not brand_name or not brand_name.strip():
            return Err("Brand name cannot be empty")
        return Ok(
            Brand(
                id=str(uuid4()), brand_name=brand_name, api_hash_key=str(uuid4()), created_at=datetime.now(timezone.utc)
            )
        )
