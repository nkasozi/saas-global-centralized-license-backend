from typing import List

from result import Err, Ok, Result

from src.core.models.licence_key import LicenseKey
from src.infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository


class LicenseKeyRepository(InMemoryRepository[LicenseKey]):
    def get_by_key_string(self, key_string: str) -> Result[LicenseKey, str]:
        matching_keys = [k for k in self._storage.values() if k.key_string == key_string]

        if not matching_keys:
            return Err(f"License key '{key_string}' not found")

        return Ok(matching_keys[0])

    def get_by_brand_id(self, brand_id: str) -> Result[List[LicenseKey], str]:
        keys_for_brand = [k for k in self._storage.values() if k.brand_id == brand_id]
        return Ok(keys_for_brand)

    def get_by_end_product_user_id(self, end_product_user_id: str) -> Result[List[LicenseKey], str]:
        keys_for_user = [k for k in self._storage.values() if k.end_product_user_id == end_product_user_id]
        return Ok(keys_for_user)

    def add_license_to_key(self, license_key_id: str, license_id: str) -> Result[LicenseKey, str]:
        key_result = self.get_by_id(license_key_id)

        if key_result.is_err():
            return key_result

        license_key = key_result.ok_value
        if license_id not in license_key.license_ids:
            license_key.license_ids.append(license_id)

        return self.save(license_key)
