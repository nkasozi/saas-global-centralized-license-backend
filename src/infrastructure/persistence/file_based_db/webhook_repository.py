from src.core.models.webhook import Webhook
from src.infrastructure.persistence.file_based_db.file_repository import FileRepository


class WebhookRepository(FileRepository[Webhook]):
    def __init__(self):
        super().__init__("data/webhooks.json", Webhook)

    def get_by_brand_id(self, brand_id: str):
        all_webhooks_result = self.get_all()
        if all_webhooks_result.is_err():
            return all_webhooks_result

        brand_webhooks = [w for w in all_webhooks_result.ok_value if w.brand_id == brand_id]
        return all_webhooks_result.__class__(brand_webhooks)
