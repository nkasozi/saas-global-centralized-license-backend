from datetime import datetime

from src.core.models.model import Model


class EndProductUser (Model):
    id: int
    user_email: str
    user_token: str
    created_at: datetime