from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from result import Err, Ok, Result

from src.core.models.model import Model


@dataclass
class Product(Model):
    brand_id: str = ""
    product_name: str = ""
    max_seats: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(brand_id: str, product_name: str, max_seats: int) -> Result["Product", str]:
        if not brand_id or not brand_id.strip():
            return Err("Brand ID cannot be empty")
        if not product_name or not product_name.strip():
            return Err("Product name cannot be empty")
        if max_seats < 0:
            return Err("Max seats cannot be negative")
        return Ok(
            Product(
                id=str(uuid4()),
                brand_id=brand_id,
                product_name=product_name,
                max_seats=max_seats,
                created_at=datetime.now(timezone.utc),
            )
        )
