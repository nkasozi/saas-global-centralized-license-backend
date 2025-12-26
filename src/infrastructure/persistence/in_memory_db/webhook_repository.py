from infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository
from src.core.models.webhook import Webhook


class WebhookRepository(InMemoryRepository[Webhook]):
    pass
