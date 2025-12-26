from typing import List

from result import Err, Ok, Result

from src.core.ports.logger_interface import LoggerInterface
from src.core.services.manager_interface import Manager


class LicenseStatusQueryService(Manager):
    def __init__(
        self,
        license_key_repository,
        license_repository,
        activation_repository,
        product_repository,
        logger: LoggerInterface,
    ):
        self.license_key_repository = license_key_repository
        self.license_repository = license_repository
        self.activation_repository = activation_repository
        self.product_repository = product_repository
        self.logger = logger

    def get_license_key_status(self, license_key_string: str) -> Result[dict, str]:
        license_key_result = self.license_key_repository.get_by_key_string(license_key_string)
        if license_key_result.is_err():
            error_message = f"License key not found: {license_key_string}"
            self.logger.error(error_message)
            return Err(error_message)

        license_key = license_key_result.ok_value
        licenses_data = self._get_licenses_data(license_key.license_ids)
        activations_result = self.activation_repository.get_by_license_key_id(license_key.id)
        activations = activations_result.ok_value if activations_result.is_ok() else []

        status_data = {
            "license_key_id": license_key.id,
            "key_string": license_key.key_string,
            "created_at": license_key.created_at.isoformat(),
            "is_valid": self._is_key_valid(license_key.license_ids),
            "licenses": licenses_data,
            "activations": [
                {
                    "activation_id": a.id,
                    "instance_id": a.instance_id,
                    "instance_id_type": a.instance_id_type.value,
                    "activated_at": a.activated_at.isoformat(),
                }
                for a in activations
            ],
        }

        self.logger.info(f"Status retrieved for license key {license_key_string}")
        return Ok(status_data)

    def get_licenses_by_customer_email(self, customer_email: str, brand_id: str) -> Result[List[dict], str]:
        license_keys_result = self.license_key_repository.get_by_brand_id(brand_id)
        if license_keys_result.is_err():
            return license_keys_result

        customer_keys = [k for k in license_keys_result.ok_value if k.end_product_user_id]

        licenses_list = []
        for license_key in customer_keys:
            key_status_result = self.get_license_key_status(license_key.key_string)
            if key_status_result.is_ok():
                licenses_list.append(key_status_result.ok_value)

        self.logger.info(
            f"Retrieved {len(licenses_list)} license keys for customer {customer_email} in brand {brand_id}"
        )
        return Ok(licenses_list)

    def get_all_brand_licenses(self, brand_id: str) -> Result[List[dict], str]:
        license_keys_result = self.license_key_repository.get_by_brand_id(brand_id)
        if license_keys_result.is_err():
            return license_keys_result

        licenses_list = []
        for license_key in license_keys_result.ok_value:
            key_status_result = self.get_license_key_status(license_key.key_string)
            if key_status_result.is_ok():
                licenses_list.append(key_status_result.ok_value)

        self.logger.info(f"Retrieved {len(licenses_list)} total license keys for brand {brand_id}")
        return Ok(licenses_list)

    def _get_licenses_data(self, license_ids: List[str]) -> List[dict]:
        licenses_data = []
        for license_id in license_ids:
            license_result = self.license_repository.get_by_id(license_id)
            if license_result.is_ok():
                license_obj = license_result.ok_value
                product_result = self.product_repository.get_by_id(license_obj.product_id)
                product_name = product_result.ok_value.product_name if product_result.is_ok() else "Unknown"

                licenses_data.append(
                    {
                        "license_id": license_obj.id,
                        "product_id": license_obj.product_id,
                        "product_name": product_name,
                        "status": license_obj.status,
                        "expires_at": license_obj.expires_at.isoformat(),
                        "is_active": license_obj.is_active(),
                    }
                )
        return licenses_data

    def _is_key_valid(self, license_ids: List[str]) -> bool:
        for license_id in license_ids:
            license_result = self.license_repository.get_by_id(license_id)
            if license_result.is_err():
                return False
            if not license_result.ok_value.is_active():
                return False
        return True
