from result import Err, Ok, Result

from src.core.models.brand import Brand
from src.core.models.licence_key import LicenseKey
from src.core.ports.auth_interface import AuthInterface
from src.core.ports.logger_interface import LoggerInterface
from src.core.ports.repository_interface import RepositoryInterface


class AuthService(AuthInterface):
    def __init__(
        self,
        brand_repository: RepositoryInterface[Brand],
        license_key_repository: RepositoryInterface[LicenseKey],
        logger: LoggerInterface,
    ):
        self.brand_repository = brand_repository
        self.license_key_repository = license_key_repository
        self.logger = logger

    def validate_brand_api_key(self, api_key: str) -> Result[str, str]:
        if not api_key:
            self.logger.warning("Brand API key validation failed: Invalid format")
            return Err("Invalid API key format")

        all_brands_result = self.brand_repository.get_all()
        if all_brands_result.is_err():
            return all_brands_result

        all_brands = all_brands_result.ok_value
        self.logger.warning(f"Validating brand API key against {len(all_brands)} brands")
        self.logger.warning(f"All brands: {all_brands}")
        matching_brand = next((brand for brand in all_brands if brand.api_hash_key == api_key), None)

        if not matching_brand:
            self.logger.warning("Brand API key validation failed: Key not found")
            return Err("API key not found or invalid")

        self.logger.debug(f"Brand {matching_brand.id} validated with API key")
        return Ok(matching_brand.id)

    def validate_license_key(self, license_key: str) -> Result[str, str]:
        if not license_key:
            self.logger.warning("License key validation failed: Empty key")
            return Err("License key is required")

        all_keys_result = self.license_key_repository.get_all()
        if all_keys_result.is_err():
            return all_keys_result

        all_keys = all_keys_result.ok_value
        matching_key = next((key for key in all_keys if key.key_string == license_key), None)

        if not matching_key:
            self.logger.warning("License key validation failed: Key not found")
            return Err("License key not found or invalid")

        self.logger.debug(f"License key {matching_key.id} validated")
        return Ok(matching_key.id)

    def get_brand_id_from_key(self, api_key: str) -> Result[str, str]:
        return self.validate_brand_api_key(api_key)
