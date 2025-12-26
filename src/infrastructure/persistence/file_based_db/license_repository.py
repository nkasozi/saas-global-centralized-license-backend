from result import Ok, Result

from src.core.models.licence import License
from src.infrastructure.persistence.file_based_db.file_repository import FileRepository


class LicenseRepository(FileRepository[License]):
    def __init__(self):
        super().__init__("data/licenses.json", License)

    def get_by_product_id(self, product_id: str) -> Result[list[License], str]:
        all_licenses_result = self.get_all()
        if all_licenses_result.is_err():
            return all_licenses_result

        product_licenses = [l for l in all_licenses_result.ok_value if l.product_id == product_id]
        return Ok(product_licenses)

    def get_by_status(self, status) -> Result[list[License], str]:
        all_licenses_result = self.get_all()
        if all_licenses_result.is_err():
            return all_licenses_result

        status_licenses = [l for l in all_licenses_result.ok_value if l.status == status]
        return Ok(status_licenses)
