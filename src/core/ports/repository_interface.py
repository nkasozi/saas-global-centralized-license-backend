from abc import abstractmethod, ABC
from typing import Optional

from src.core.models.model import Model


class RepositoryInterface(ABC):
    @abstractmethod
    def save(self, model: Model)->bool:
        pass

    def get_by_id(self, id: int)-> Optional[Model]:
        pass

    def delete_by_id(self, id: int)->bool:
        pass