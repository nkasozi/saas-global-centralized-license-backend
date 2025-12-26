from typing import List

from result import Err, Ok, Result

from src.core.models.audit_log import AuditOperation
from src.core.models.brand import Brand
from src.core.ports.logger_interface import LoggerInterface
from src.core.ports.repository_interface import RepositoryInterface
from src.core.services.audit_service import AuditService
from src.core.services.manager_interface import Manager


class BrandManager(Manager):
    def __init__(
        self, brand_repository: RepositoryInterface[Brand], audit_service: AuditService, logger: LoggerInterface
    ):
        self.brand_repository = brand_repository
        self.audit_service = audit_service
        self.logger = logger

    def create_brand(self, brand_name: str) -> Result[Brand, str]:
        brand_creation_result = Brand.create(brand_name)

        if brand_creation_result.is_err():
            return brand_creation_result

        brand = brand_creation_result.ok_value
        saved_brand_result = self.brand_repository.save(brand)

        if saved_brand_result.is_ok():
            saved_brand = saved_brand_result.ok_value
            self.audit_service.log_operation(
                brand_id=saved_brand.id,
                operation=AuditOperation.BRAND_CREATED,
                resource_id=saved_brand.id,
                resource_type="brand",
                changes={"brand_name": saved_brand.brand_name},
            )

            all_brands = self.brand_repository.get_all()
            self.logger.warning(f"All brands: {all_brands}")

        return saved_brand_result

    def get_brand_by_id(self, brand_id: str) -> Result[Brand, str]:
        return self.brand_repository.get_by_id(brand_id)

    def get_brand_by_api_key(self, api_key: str) -> Result[Brand, str]:
        all_brands_result = self.brand_repository.get_all()
        if all_brands_result.is_err():
            return all_brands_result
        all_brands = all_brands_result.ok_value
        matching_brands = [brand for brand in all_brands if brand.api_hash_key == api_key]
        if not matching_brands:
            return Err("Brand not found")
        return Ok(matching_brands[0])

    def get_all_brands(self) -> Result[List[Brand], str]:
        return self.brand_repository.get_all()
