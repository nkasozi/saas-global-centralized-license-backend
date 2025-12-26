from datetime import datetime
from typing import List

from src.core.models.model import Model


class LicenseKey (Model):
    id: int
    brand_id: int
    license_ids: List[int]
    key_string: str
    end_product_user_id: int
    created_at: datetime