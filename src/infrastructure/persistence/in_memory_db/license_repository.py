from typing import List

from result import Ok, Result

from src.core.models.licence import License
from src.infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository


class LicenseRepository(InMemoryRepository[License]):
    def get_by_product_id(self, product_id: str) -> Result[List[License], str]:
        licenses_for_product = [l for l in self._storage.values() if l.product_id == product_id]
        return Ok(licenses_for_product)

    def get_active_by_product_id(self, product_id: str) -> Result[List[License], str]:
        active_licenses = [l for l in self._storage.values() if l.product_id == product_id and l.is_active()]
        return Ok(active_licenses)
