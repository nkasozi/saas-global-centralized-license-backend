from unittest.mock import Mock
from uuid import uuid4

import pytest
from result import Err, Ok

from src.core.models.webhook import Webhook, WebhookEvent, WebhookStatus
from src.core.services.webhook_service import WebhookService


@pytest.fixture
def webhook_repository() -> Mock:
    return Mock()


@pytest.fixture
def logger() -> Mock:
    return Mock()


@pytest.fixture
def webhook_service(webhook_repository: Mock, logger: Mock) -> WebhookService:
    return WebhookService(webhook_repository, logger)


@pytest.fixture
def test_webhook() -> Webhook:
    brand_id = str(uuid4())
    webhook_result = Webhook.create(
        brand_id=brand_id,
        url="https://example.com/webhook",
        events=[WebhookEvent.LICENSE_PROVISIONED],
        secret="secret-key-1234",
    )
    webhook = webhook_result.unwrap()
    return webhook


class TestWebhookService:
    def test_create_webhook_success(self, webhook_service: WebhookService, webhook_repository: Mock) -> None:
        brand_id = str(uuid4())
        webhook_result = Webhook.create(
            brand_id=brand_id,
            url="https://example.com/hook",
            events=[WebhookEvent.LICENSE_ACTIVATED],
            secret="secret12345678",
        )
        webhook = webhook_result.unwrap()
        webhook_repository.save.return_value = Ok(webhook)

        result = webhook_service.create_webhook(
            brand_id=brand_id,
            url="https://example.com/hook",
            events=[WebhookEvent.LICENSE_ACTIVATED],
            secret="secret12345678",
        )

        assert result.is_ok()
        webhook_repository.save.assert_called_once()

    def test_create_webhook_invalid_url(self, webhook_service: WebhookService) -> None:
        result = webhook_service.create_webhook(
            brand_id=str(uuid4()),
            url="not-a-url",
            events=[WebhookEvent.LICENSE_PROVISIONED],
            secret="secret12345678",
        )

        assert result.is_err()
        assert "http" in result.unwrap_err().lower()

    def test_create_webhook_no_events(self, webhook_service: WebhookService) -> None:
        result = webhook_service.create_webhook(
            brand_id=str(uuid4()),
            url="https://example.com/hook",
            events=[],
            secret="secret12345678",
        )

        assert result.is_err()

    def test_create_webhook_weak_secret(self, webhook_service: WebhookService) -> None:
        result = webhook_service.create_webhook(
            brand_id=str(uuid4()),
            url="https://example.com/hook",
            events=[WebhookEvent.LICENSE_PROVISIONED],
            secret="weak",
        )

        assert result.is_err()
        assert "8 characters" in result.unwrap_err().lower()

    def test_update_webhook_success(
        self, webhook_service: WebhookService, webhook_repository: Mock, test_webhook: Webhook
    ) -> None:
        webhook_repository.get_by_id.return_value = Ok(test_webhook)
        webhook_repository.save.return_value = Ok(test_webhook)

        result = webhook_service.update_webhook(
            webhook_id=test_webhook.id,
            url="https://new-url.com/hook",
        )

        assert result.is_ok()
        webhook_repository.save.assert_called_once()

    def test_update_webhook_not_found(self, webhook_service: WebhookService, webhook_repository: Mock) -> None:
        webhook_id = str(uuid4())
        webhook_repository.get_by_id.return_value = Err("Not found")

        result = webhook_service.update_webhook(webhook_id=webhook_id, url="https://example.com/hook")

        assert result.is_err()
        assert "not found" in result.unwrap_err().lower()

    def test_update_webhook_invalid_url(
        self, webhook_service: WebhookService, webhook_repository: Mock, test_webhook: Webhook
    ) -> None:
        webhook_repository.get_by_id.return_value = Ok(test_webhook)

        result = webhook_service.update_webhook(webhook_id=test_webhook.id, url="invalid-url")

        assert result.is_err()

    def test_delete_webhook_success(
        self, webhook_service: WebhookService, webhook_repository: Mock, test_webhook: Webhook
    ) -> None:
        webhook_id = test_webhook.id
        webhook_repository.get_by_id.return_value = Ok(test_webhook)
        webhook_repository.delete_by_id.return_value = Ok(True)

        result = webhook_service.delete_webhook(webhook_id=webhook_id)

        assert result.is_ok()
        webhook_repository.delete_by_id.assert_called_once_with(webhook_id)

    def test_delete_webhook_not_found(self, webhook_service: WebhookService, webhook_repository: Mock) -> None:
        webhook_id = str(uuid4())
        webhook_repository.delete_by_id.return_value = Err("Not found")

        result = webhook_service.delete_webhook(webhook_id=webhook_id)

        assert result.is_err()
        assert "not found" in result.unwrap_err().lower()

    def test_get_brand_webhooks_success(
        self, webhook_service: WebhookService, webhook_repository: Mock, test_webhook: Webhook
    ) -> None:
        webhook_repository.get_all.return_value = Ok([test_webhook])

        result = webhook_service.get_brand_webhooks(test_webhook.brand_id)

        assert result.is_ok()
        webhooks = result.unwrap()
        assert isinstance(webhooks, list)
        assert len(webhooks) == 1
        assert webhooks[0].brand_id == test_webhook.brand_id

    def test_get_brand_webhooks_filters_by_brand(
        self, webhook_service: WebhookService, webhook_repository: Mock
    ) -> None:
        brand_id_1 = str(uuid4())
        webhook1_result = Webhook.create(
            brand_id_1, "https://example.com/1", [WebhookEvent.LICENSE_PROVISIONED], "secret1234567"
        )
        webhook1 = webhook1_result.unwrap()
        webhook_repository.get_all.return_value = Ok([webhook1])

        result = webhook_service.get_brand_webhooks(brand_id=brand_id_1)

        assert result.is_ok()
        webhooks = result.unwrap()
        assert isinstance(webhooks, list)
        assert len(webhooks) == 1
        assert webhooks[0].brand_id == brand_id_1

    def test_get_webhooks_for_event_success(
        self, webhook_service: WebhookService, webhook_repository: Mock, test_webhook: Webhook
    ) -> None:
        test_webhook.status = WebhookStatus.ACTIVE
        test_webhook.failure_count = 0
        webhook_repository.get_all.return_value = Ok([test_webhook])

        result = webhook_service.get_webhooks_for_event(
            brand_id=test_webhook.brand_id,
            event=WebhookEvent.LICENSE_PROVISIONED,
        )

        assert result.is_ok()
        webhooks = result.unwrap()
        assert isinstance(webhooks, list)
        assert len(webhooks) == 1

    def test_get_webhooks_for_event_filters_inactive(
        self, webhook_service: WebhookService, webhook_repository: Mock, test_webhook: Webhook
    ) -> None:
        test_webhook.status = WebhookStatus.FAILED
        test_webhook.failure_count = 5
        webhook_repository.get_all.return_value = Ok([test_webhook])

        result = webhook_service.get_webhooks_for_event(
            brand_id=test_webhook.brand_id,
            event=WebhookEvent.LICENSE_PROVISIONED,
        )

        assert result.is_ok()
        webhooks = result.unwrap()
        assert isinstance(webhooks, list)
        assert len(webhooks) == 0

    def test_build_webhook_payload(self, webhook_service: WebhookService) -> None:
        resource_id = str(uuid4())
        payload = webhook_service.build_webhook_payload(
            event=WebhookEvent.LICENSE_PROVISIONED,
            resource_id=resource_id,
            resource_data={"seats": 5},
        )

        assert payload["event"] == WebhookEvent.LICENSE_PROVISIONED.value
        assert payload["resource_id"] == resource_id
        assert payload["data"]["seats"] == 5
        assert "timestamp" in payload

    def test_trigger_webhooks_success(
        self, webhook_service: WebhookService, webhook_repository: Mock, test_webhook: Webhook
    ) -> None:
        test_webhook.status = WebhookStatus.ACTIVE
        test_webhook.failure_count = 0
        test_webhook.brand_id = str(uuid4())
        webhook_repository.get_all.return_value = Ok([test_webhook])
        webhook_repository.save.return_value = Ok(test_webhook)

        result = webhook_service.trigger_webhooks(
            brand_id=test_webhook.brand_id,
            event=WebhookEvent.LICENSE_PROVISIONED,
            resource_id=str(uuid4()),
            resource_data={"seats": 5},
        )

        assert result.is_ok()
        count = result.unwrap()
        assert count >= 0

    def test_trigger_webhooks_no_matching_webhooks(
        self, webhook_service: WebhookService, webhook_repository: Mock
    ) -> None:
        webhook_repository.get_all.return_value = Ok([])

        result = webhook_service.trigger_webhooks(
            brand_id=str(uuid4()),
            event=WebhookEvent.LICENSE_PROVISIONED,
            resource_id=str(uuid4()),
            resource_data={},
        )

        assert result.is_ok()
        assert result.unwrap() == 0

    def test_dispatch_webhook_success(self, webhook_service: WebhookService, test_webhook: Webhook) -> None:
        payload = {"event": "test", "data": {}}

        result = webhook_service.dispatch_webhook(test_webhook, payload)

        assert result is True

    def test_deactivate_failed_webhook_success(
        self, webhook_service: WebhookService, webhook_repository: Mock, test_webhook: Webhook
    ) -> None:
        test_webhook.failure_count = 4
        webhook_repository.get_by_id.return_value = Ok(test_webhook)
        webhook_repository.save.return_value = Ok(test_webhook)

        result = webhook_service.deactivate_failed_webhook(webhook_id=test_webhook.id)

        assert result.is_ok()
        webhook_repository.save.assert_called_once()

    def test_deactivate_failed_webhook_not_found(
        self, webhook_service: WebhookService, webhook_repository: Mock
    ) -> None:
        webhook_id = str(uuid4())
        webhook_repository.get_by_id.return_value = Err("Not found")

        result = webhook_service.deactivate_failed_webhook(webhook_id=webhook_id)

        assert result.is_err()
        assert "not found" in result.unwrap_err().lower()

    def test_webhook_is_active_when_status_active_and_low_failures(
        self, webhook_service: WebhookService, test_webhook: Webhook
    ) -> None:
        test_webhook.status = WebhookStatus.ACTIVE
        test_webhook.failure_count = 2
        test_webhook.max_failures = 5

        assert test_webhook.is_active() is True

    def test_webhook_is_not_active_when_failed(self, webhook_service: WebhookService, test_webhook: Webhook) -> None:
        test_webhook.status = WebhookStatus.FAILED
        test_webhook.failure_count = 5

        assert test_webhook.is_active() is False

    def test_webhook_record_failure_increments_count(
        self, webhook_service: WebhookService, test_webhook: Webhook
    ) -> None:
        initial_count = test_webhook.failure_count
        test_webhook.record_failure()

        assert test_webhook.failure_count == initial_count + 1

    def test_webhook_reset_failure_count(self, webhook_service: WebhookService, test_webhook: Webhook) -> None:
        test_webhook.failure_count = 3
        test_webhook.reset_failure_count()

        assert test_webhook.failure_count == 0
        assert test_webhook.status == WebhookStatus.ACTIVE

    def test_create_multiple_event_subscription(
        self, webhook_service: WebhookService, webhook_repository: Mock
    ) -> None:
        brand_id = str(uuid4())
        events = [
            WebhookEvent.LICENSE_PROVISIONED,
            WebhookEvent.LICENSE_ACTIVATED,
            WebhookEvent.LICENSE_SUSPENDED,
        ]
        webhook_result = Webhook.create(
            brand_id=brand_id,
            url="https://example.com/hook",
            events=events,
            secret="secret12345678",
        )
        webhook = webhook_result.unwrap()
        webhook_repository.save.return_value = Ok(webhook)

        result = webhook_service.create_webhook(
            brand_id=brand_id,
            url="https://example.com/hook",
            events=events,
            secret="secret12345678",
        )

        assert result.is_ok()
        assert len(result.unwrap().events) == 3
