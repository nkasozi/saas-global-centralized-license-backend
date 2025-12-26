from datetime import datetime

from result import Err, Ok, Result

from src.core.models.audit_log import AuditOperation
from src.core.models.licence import License
from src.core.models.licence_key import LicenseKey
from src.core.models.webhook import WebhookEvent
from src.core.ports.logger_interface import LoggerInterface
from src.core.services.manager_interface import Manager


class LicenseProvisioningService(Manager):
    def __init__(
        self,
        license_repository,
        license_key_repository,
        product_repository,
        webhook_service,
        audit_service,
        logger: LoggerInterface,
    ):
        self.license_repository = license_repository
        self.license_key_repository = license_key_repository
        self.product_repository = product_repository
        self.webhook_service = webhook_service
        self.audit_service = audit_service
        self.logger = logger

    def provision_license_for_product(
        self, product_id: str, brand_id: str, end_product_user_id: str, expiration_date: datetime
    ) -> Result[tuple[License, LicenseKey], str]:
        product_result = self.product_repository.get_by_id(product_id)
        if product_result.is_err():
            error_message = f"Product {product_id} not found"
            self.logger.error(error_message)
            return Err(error_message)

        license_creation_result = License.create(product_id, expiration_date)
        if license_creation_result.is_err():
            self.logger.error(f"License creation failed: {license_creation_result.err_value}")
            return license_creation_result

        license_obj = license_creation_result.ok_value
        saved_license_result = self.license_repository.save(license_obj)
        if saved_license_result.is_err():
            return saved_license_result

        saved_license = saved_license_result.ok_value

        license_key_creation_result = LicenseKey.create(brand_id, end_product_user_id)
        if license_key_creation_result.is_err():
            return license_key_creation_result

        license_key = license_key_creation_result.ok_value
        license_key.license_ids.append(saved_license.id)
        saved_key_result = self.license_key_repository.save(license_key)
        if saved_key_result.is_err():
            return saved_key_result

        saved_key = saved_key_result.ok_value
        self.logger.info(f"License provisioned: {saved_license.id} for product {product_id}")

        self.audit_service.log_operation(
            brand_id=brand_id,
            operation=AuditOperation.LICENSE_PROVISIONED,
            resource_id=saved_license.id,
            resource_type="license",
            changes={"license_key_id": saved_key.id, "product_id": product_id},
        )

        self.product_repository.get_by_id(product_id).ok_value
        self.webhook_service.trigger_webhooks(
            brand_id=brand_id,
            event=WebhookEvent.LICENSE_PROVISIONED,
            resource_id=saved_license.id,
            resource_data=saved_license.to_dict() if hasattr(saved_license, "to_dict") else {"id": saved_license.id},
        )

        return Ok((saved_license, saved_key))

    def add_license_to_existing_key(
        self, license_key_id: str, product_id: str, expiration_date: datetime
    ) -> Result[License, str]:
        license_key_result = self.license_key_repository.get_by_id(license_key_id)
        if license_key_result.is_err():
            error_message = f"License key {license_key_id} not found"
            self.logger.error(error_message)
            return Err(error_message)

        product_result = self.product_repository.get_by_id(product_id)
        if product_result.is_err():
            error_message = f"Product {product_id} not found"
            self.logger.error(error_message)
            return Err(error_message)

        license_creation_result = License.create(product_id, expiration_date)
        if license_creation_result.is_err():
            return license_creation_result

        license_obj = license_creation_result.ok_value
        saved_license_result = self.license_repository.save(license_obj)
        if saved_license_result.is_err():
            return saved_license_result

        saved_license = saved_license_result.ok_value
        license_key = license_key_result.ok_value
        license_key.license_ids.append(saved_license.id)
        self.license_key_repository.save(license_key)

        self.audit_service.log_operation(
            brand_id=license_key.brand_id,
            operation=AuditOperation.LICENSE_PROVISIONED,
            resource_id=saved_license.id,
            resource_type="license",
            changes={"license_key_id": license_key_id, "product_id": product_id},
        )

        self.logger.info(f"License {saved_license.id} added to key {license_key_id}")
        return Ok(saved_license)
