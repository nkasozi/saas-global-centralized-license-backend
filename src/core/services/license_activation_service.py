from typing import List

from result import Err, Ok, Result

from src.core.models.activation import Activation, InstanceIDType
from src.core.models.audit_log import AuditOperation
from src.core.models.webhook import WebhookEvent
from src.core.ports.logger_interface import LoggerInterface
from src.core.services.manager_interface import Manager


class LicenseActivationService(Manager):
    def __init__(
        self,
        activation_repository,
        license_key_repository,
        license_repository,
        product_repository,
        webhook_service,
        audit_service,
        logger: LoggerInterface,
    ):
        self.activation_repository = activation_repository
        self.license_key_repository = license_key_repository
        self.license_repository = license_repository
        self.product_repository = product_repository
        self.webhook_service = webhook_service
        self.audit_service = audit_service
        self.logger = logger

    def activate_license_for_instance(
        self, license_key_string: str, instance_id_type: InstanceIDType, instance_id: str, ip_address: str
    ) -> Result[Activation, str]:
        license_key_result = self.license_key_repository.get_by_key_string(license_key_string)
        if license_key_result.is_err():
            error_message = f"License key not found: {license_key_string}"
            self.logger.error(error_message)
            return Err(error_message)

        license_key = license_key_result.ok_value
        licenses_valid = self._verify_all_licenses_active(license_key.license_ids)
        if not licenses_valid:
            error_message = f"One or more licenses are not active for key {license_key_string}"
            self.logger.warning(error_message)
            return Err(error_message)

        activation_count_check = self._verify_product_activation_limit(license_key.license_ids)
        if activation_count_check.is_err():
            return activation_count_check

        existing_activation_result = self.activation_repository.get_by_license_key_id_and_instance_id(
            license_key.id, instance_id
        )
        if existing_activation_result.is_ok():
            error_message = (
                f"Instance {instance_id} is already activated for this license. Please use a unique instance ID."
            )
            self.logger.warning(error_message)
            return Err(error_message)

        activation_creation_result = Activation.create(license_key.id, instance_id_type, instance_id, ip_address)
        if activation_creation_result.is_err():
            return activation_creation_result

        activation = activation_creation_result.ok_value
        saved_activation_result = self.activation_repository.save(activation)
        if saved_activation_result.is_err():
            return saved_activation_result

        saved_activation = saved_activation_result.ok_value
        self.logger.info(f"Instance {instance_id} activated for license key {license_key_string}")

        self.audit_service.log_operation(
            brand_id=license_key.brand_id,
            operation=AuditOperation.LICENSE_ACTIVATED,
            resource_id=saved_activation.id,
            resource_type="activation",
            changes={"license_key_id": license_key.id, "instance_id": instance_id},
        )

        self.webhook_service.trigger_webhooks(
            brand_id=license_key.brand_id,
            event=WebhookEvent.LICENSE_ACTIVATED,
            resource_id=saved_activation.id,
            resource_data=(
                saved_activation.to_dict() if hasattr(saved_activation, "to_dict") else {"id": saved_activation.id}
            ),
        )

        return Ok(saved_activation)

    def deactivate_instance(self, activation_id: str) -> Result[bool, str]:
        activation_result = self.activation_repository.get_by_id(activation_id)
        if activation_result.is_err():
            error_message = f"Activation {activation_id} not found"
            self.logger.error(error_message)
            return Err(error_message)

        activation = activation_result.ok_value
        license_key_result = self.license_key_repository.get_by_id(activation.license_key_id)
        license_key = license_key_result.ok_value if license_key_result.is_ok() else None

        delete_result = self.activation_repository.delete_by_id(activation_id)
        if delete_result.is_err():
            return delete_result

        self.logger.info(f"Activation {activation_id} deactivated")

        if license_key:
            self.audit_service.log_operation(
                brand_id=license_key.brand_id,
                operation=AuditOperation.LICENSE_DEACTIVATED,
                resource_id=activation_id,
                resource_type="activation",
                changes={"license_key_id": license_key.id},
            )

            self.webhook_service.trigger_webhooks(
                brand_id=license_key.brand_id,
                event=WebhookEvent.LICENSE_DEACTIVATED,
                resource_id=activation_id,
                resource_data={"id": activation_id},
            )

        return Ok(True)

    def _verify_all_licenses_active(self, license_ids: List[str]) -> bool:
        for license_id in license_ids:
            license_result = self.license_repository.get_by_id(license_id)
            if license_result.is_err():
                return False
            license_obj = license_result.ok_value
            if not license_obj.is_active():
                return False
        return True

    def _verify_product_activation_limit(self, license_ids: List[str]) -> Result[bool, str]:
        if not license_ids:
            return Ok(True)

        all_activations_count = 0

        for license_id in license_ids:
            license_result = self.license_repository.get_by_id(license_id)
            if license_result.is_err():
                continue

            license_obj = license_result.ok_value
            product_result = self.product_repository.get_by_id(license_obj.product_id)
            if product_result.is_err():
                error_message = f"Product {license_obj.product_id} not found"
                self.logger.error(error_message)
                return Err(error_message)

            product = product_result.ok_value
            product_activations = self._count_product_activations(license_obj.product_id)
            all_activations_count += product_activations

            if all_activations_count >= product.max_seats:
                error_message = (
                    f"Product {product.product_name} has reached maximum activation limit of {product.max_seats}"
                )
                self.logger.warning(error_message)
                return Err(error_message)

        return Ok(True)

    def _count_product_activations(self, product_id: str) -> int:
        all_activations_result = self.activation_repository.get_all()
        if all_activations_result.is_err():
            self.logger.warning(f"Could not retrieve activations for product {product_id}")
            return 0

        activations = all_activations_result.ok_value
        product_activation_count = 0

        for activation in activations:
            license_key_result = self.license_key_repository.get_by_id(activation.license_key_id)
            if license_key_result.is_err():
                continue

            license_key = license_key_result.ok_value

            for license_id in license_key.license_ids:
                license_result = self.license_repository.get_by_id(license_id)
                if license_result.is_err():
                    error_message = f"Could not retrieve license {license_id} for activation counting: {license_result.unwrap_err()}"
                    self.logger.warning(error_message)
                    continue

                license_obj = license_result.ok_value
                if license_obj.product_id == product_id:
                    product_activation_count += 1
                    break

        return product_activation_count
