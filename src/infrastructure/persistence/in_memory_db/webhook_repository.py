from src.core.models.webhook import Webhook
from src.infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository


class WebhookRepository(InMemoryRepository[Webhook]):
    pass
