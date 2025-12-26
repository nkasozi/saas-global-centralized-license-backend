import json
from datetime import datetime, timezone
from typing import Optional

from result import Err, Ok, Result

from src.core.models.webhook import Webhook, WebhookEvent
from src.core.ports.logger_interface import LoggerInterface


class WebhookService:
    def __init__(
        self,
        webhook_repository,
        logger: LoggerInterface,
    ):
        self.webhook_repository = webhook_repository
        self.logger = logger

    def validate_webhook_events(self, events: list[str]) -> Result[list, str]:
        if not events:
            return Err("At least one webhook event is required")

        valid_events = [e.value for e in WebhookEvent]
        converted_events = []
        invalid_events = []

        for event in events:
            try:
                converted_events.append(WebhookEvent(event))
            except ValueError:
                invalid_events.append(event)

        if invalid_events:
            return Err(
                f"Invalid webhook events: {', '.join(invalid_events)}. "
                f"Acceptable events are: {', '.join(valid_events)}"
            )

        return Ok(converted_events)

    def create_webhook(
        self,
        brand_id: str,
        url: str,
        events: list[WebhookEvent],
        secret: str,
    ) -> Result[Webhook, str]:
        webhook_result = Webhook.create(brand_id, url, events, secret)

        if webhook_result.is_err():
            self.logger.error(f"Failed to create webhook: {webhook_result.unwrap_err()}")
            return webhook_result

        webhook = webhook_result.unwrap()
        save_result = self.webhook_repository.save(webhook)

        if save_result.is_err():
            self.logger.error(f"Failed to save webhook: {save_result.unwrap_err()}")
            return save_result

        saved_webhook = save_result.unwrap()
        self.logger.info(f"Webhook created for brand {brand_id}: {saved_webhook.id}")
        return Ok(saved_webhook)

    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[list[WebhookEvent]] = None,
        secret: Optional[str] = None,
    ) -> Result[Webhook, str]:
        webhook_result = self.webhook_repository.get_by_id(webhook_id)

        if webhook_result.is_err():
            return Err(f"Webhook {webhook_id} not found")

        webhook = webhook_result.unwrap()

        if url:
            if not url.startswith(("http://", "https://")):
                return Err("URL must start with http:// or https://")
            webhook.url = url

        if events:
            if not events:
                return Err("At least one event must be subscribed")
            webhook.events = events

        if secret:
            if len(secret) < 8:
                return Err("Secret must be at least 8 characters")
            webhook.secret = secret

        webhook.updated_at = datetime.now(timezone.utc)

        update_result = self.webhook_repository.save(webhook)

        if update_result.is_err():
            self.logger.error(f"Failed to update webhook: {update_result.unwrap_err()}")
            return update_result

        self.logger.info(f"Webhook {webhook_id} updated")
        return Ok(update_result.unwrap())

    def delete_webhook(self, webhook_id: str) -> Result[bool, str]:
        exists_result = self.webhook_repository.get_by_id(webhook_id)

        if exists_result.is_err():
            return Err(f"Webhook {webhook_id} not found")

        delete_result = self.webhook_repository.delete_by_id(webhook_id)

        if delete_result.is_err():
            self.logger.error(f"Failed to delete webhook: {delete_result.unwrap_err()}")
            return delete_result

        self.logger.info(f"Webhook {webhook_id} deleted")
        return Ok(True)

    def get_webhook_by_id(self, webhook_id: str) -> Result[Webhook, str]:
        webhook_result = self.webhook_repository.get_by_id(webhook_id)

        if webhook_result.is_err():
            return Err(f"Webhook {webhook_id} not found")

        return webhook_result

    def get_webhooks_by_brand(self, brand_id: str) -> Result[list[Webhook], str]:
        all_webhooks_result = self.webhook_repository.get_all()

        if all_webhooks_result.is_err():
            return all_webhooks_result

        all_webhooks = all_webhooks_result.unwrap()
        brand_webhooks = [w for w in all_webhooks if w.brand_id == brand_id]

        self.logger.debug(f"Retrieved {len(brand_webhooks)} webhooks for brand {brand_id}")
        return Ok(brand_webhooks)

    def get_brand_webhooks(
        self,
        brand_id: str,
    ) -> Result[list[Webhook], str]:
        all_webhooks_result = self.webhook_repository.get_all()

        if all_webhooks_result.is_err():
            return all_webhooks_result

        all_webhooks = all_webhooks_result.unwrap()
        brand_webhooks = [w for w in all_webhooks if w.brand_id == brand_id]

        self.logger.debug(f"Retrieved {len(brand_webhooks)} webhooks for brand {brand_id}")
        return Ok(brand_webhooks)

    def get_webhooks_for_event(
        self,
        brand_id: str,
        event: WebhookEvent,
    ) -> Result[list[Webhook], str]:
        all_webhooks_result = self.webhook_repository.get_all()

        if all_webhooks_result.is_err():
            return all_webhooks_result

        all_webhooks = all_webhooks_result.unwrap()
        matching_webhooks = [w for w in all_webhooks if w.brand_id == brand_id and event in w.events and w.is_active()]

        self.logger.debug(f"Found {len(matching_webhooks)} active webhooks for {event.value} in brand {brand_id}")
        return Ok(matching_webhooks)

    def build_webhook_payload(
        self,
        event: WebhookEvent,
        resource_id: str,
        resource_data: dict,
    ) -> dict:
        return {
            "event": event.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resource_id": resource_id,
            "data": resource_data,
        }

    def trigger_webhooks(
        self,
        brand_id: str,
        event: WebhookEvent,
        resource_id: str,
        resource_data: dict,
    ) -> Result[int, str]:
        webhooks_result = self.get_webhooks_for_event(brand_id, event)

        if webhooks_result.is_err():
            return Err(webhooks_result.unwrap_err())

        webhooks = webhooks_result.unwrap()

        if not webhooks:
            self.logger.debug(f"No webhooks to trigger for {event.value} in brand {brand_id}")
            return Ok(0)

        payload = self.build_webhook_payload(event, resource_id, resource_data)
        triggered_count = 0

        for webhook in webhooks:
            success = self.dispatch_webhook(webhook, payload)
            if success:
                triggered_count += 1
                webhook.last_triggered_at = datetime.now(timezone.utc)
                webhook.reset_failure_count()
                self.webhook_repository.save(webhook)
            else:
                webhook.record_failure()
                self.webhook_repository.save(webhook)

        self.logger.info(f"Triggered {triggered_count} webhooks for {event.value} in brand {brand_id}")
        return Ok(triggered_count)

    def dispatch_webhook(self, webhook: Webhook, payload: dict) -> bool:
        try:
            json.dumps(payload)
            self.logger.debug(f"Dispatching webhook {webhook.id} to {webhook.url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to dispatch webhook {webhook.id}: {str(e)}")
            return False

    def deactivate_failed_webhook(self, webhook_id: str) -> Result[bool, str]:
        webhook_result = self.webhook_repository.get_by_id(webhook_id)

        if webhook_result.is_err():
            return Err(f"Webhook {webhook_id} not found")

        webhook = webhook_result.unwrap()
        webhook.record_failure()

        update_result = self.webhook_repository.save(webhook)

        if update_result.is_err():
            return Err(update_result.unwrap_err())

        self.logger.warning(f"Webhook {webhook_id} failure count increased to {webhook.failure_count}")
        return Ok(True)
