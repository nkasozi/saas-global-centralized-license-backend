from typing import List

from result import Result

from src.core.models.audit_log import AuditOperation
from src.core.models.product import Product
from src.core.ports.logger_interface import LoggerInterface
from src.core.services.audit_service import AuditService
from src.core.services.manager_interface import Manager


class ProductManager(Manager):
    def __init__(self, product_repository, audit_service: AuditService, logger: LoggerInterface):
        self.product_repository = product_repository
        self.audit_service = audit_service
        self.logger = logger

    def create_product(self, brand_id: str, product_name: str, max_seats: int) -> Result[Product, str]:
        product_creation_result = Product.create(brand_id, product_name, max_seats)

        if product_creation_result.is_err():
            return product_creation_result

        product = product_creation_result.ok_value
        saved_product_result = self.product_repository.save(product)

        if saved_product_result.is_ok():
            saved_product = saved_product_result.ok_value
            self.audit_service.log_operation(
                brand_id=brand_id,
                operation=AuditOperation.PRODUCT_CREATED,
                resource_id=saved_product.id,
                resource_type="product",
                changes={"product_name": saved_product.product_name, "max_seats": saved_product.max_seats},
            )

        return saved_product_result

    def get_product_by_id(self, product_id: str) -> Result[Product, str]:
        return self.product_repository.get_by_id(product_id)

    def get_products_by_brand_id(self, brand_id: str) -> Result[List[Product], str]:
        products_result = self.product_repository.get_by_brand_id(brand_id)
        return products_result

    def update_product(
        self, product_id: str, product_name: str | None = None, max_seats: int | None = None
    ) -> Result[Product, str]:
        product_result = self.product_repository.get_by_id(product_id)

        if product_result.is_err():
            return product_result

        product = product_result.ok_value

        if product_name is not None and product_name.strip():
            product.product_name = product_name

        if max_seats is not None and max_seats >= 0:
            product.max_seats = max_seats

        return self.product_repository.save(product)

    def delete_product(self, product_id: str) -> Result[str, str]:
        product_result = self.product_repository.get_by_id(product_id)

        if product_result.is_err():
            return product_result

        return self.product_repository.delete(product_id)
