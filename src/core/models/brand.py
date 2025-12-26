from datetime import datetime

from src.core.models.model import Model


class Brand (Model):
    id: int
    brand_name: str
    api_hash_key: str
    created_at: datetime