from typing import Optional

from src.core.models.brand import Brand
from src.core.services.manager_interface import Manager


class BrandManager(Manager):
    def create(self, brand: Brand)->Optional[Brand]:
        pass
