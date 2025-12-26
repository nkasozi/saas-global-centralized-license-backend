from result import Err, Ok, Result

from src.core.models.licence_key import LicenseKey
from src.infrastructure.persistence.file_based_db.file_repository import FileRepository


class LicenseKeyRepository(FileRepository[LicenseKey]):
    def __init__(self):
        super().__init__("data/license_keys.json", LicenseKey)

    def get_by_key_string(self, key_string: str) -> Result[LicenseKey, str]:
        all_keys_result = self.get_all()
        if all_keys_result.is_err():
            return all_keys_result

        matching_keys = [k for k in all_keys_result.ok_value if k.key_string == key_string]

        if not matching_keys:
            return Err(f"License key with string '{key_string}' not found")

        return Ok(matching_keys[0])

    def get_by_brand_id(self, brand_id: str) -> Result[list[LicenseKey], str]:
        all_keys_result = self.get_all()
        if all_keys_result.is_err():
            return all_keys_result

        brand_keys = [k for k in all_keys_result.ok_value if k.brand_id == brand_id]
        return Ok(brand_keys)

    def get_by_license_key_id_and_instance_id(self, license_key_id: str, instance_id: str) -> Result[LicenseKey, str]:
        all_keys_result = self.get_all()
        if all_keys_result.is_err():
            return all_keys_result

        matching_keys = [k for k in all_keys_result.ok_value if k.id == license_key_id]

        if not matching_keys:
            return Err(f"License key with id '{license_key_id}' not found")

        return Ok(matching_keys[0])
