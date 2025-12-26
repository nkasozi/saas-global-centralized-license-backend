from abc import ABC, abstractmethod

from result import Result


class AuthInterface(ABC):
    @abstractmethod
    def validate_brand_api_key(self, api_key: str) -> Result[str, str]:
        pass

    @abstractmethod
    def validate_license_key(self, license_key: str) -> Result[str, str]:
        pass

    @abstractmethod
    def get_brand_id_from_key(self, api_key: str) -> Result[str, str]:
        pass
