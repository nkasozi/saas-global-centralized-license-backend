from datetime import datetime

from src.core.models.model import Model


class Product(Model):
    id: int
    brand_id: int
    product_name: str
    max_seats: int
    created_at: datetime