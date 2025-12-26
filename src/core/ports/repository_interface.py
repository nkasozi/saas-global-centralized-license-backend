from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from result import Result

from src.core.models.model import Model

T = TypeVar("T", bound=Model)


class RepositoryInterface(ABC, Generic[T]):
    @abstractmethod
    def save(self, model: T) -> Result[T, str]:
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Result[T, str]:
        pass

    @abstractmethod
    def delete_by_id(self, entity_id: str) -> Result[bool, str]:
        pass

    @abstractmethod
    def get_all(self) -> Result[List[T], str]:
        pass
