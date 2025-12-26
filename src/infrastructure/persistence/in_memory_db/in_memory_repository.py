from threading import Lock
from typing import Dict, Generic, List, TypeVar

from result import Err, Ok, Result

from src.core.models.model import Model
from src.core.ports.repository_interface import RepositoryInterface

T = TypeVar("T", bound=Model)


class InMemoryRepository(RepositoryInterface[T], Generic[T]):
    def __init__(self):
        self._storage: Dict[str, T] = {}
        self._lock = Lock()

    def save(self, model: T) -> Result[T, str]:
        with self._lock:
            if not model.id or not model.id.strip():
                return Err("Model must have a valid ID before saving")
            self._storage[model.id] = model
            return Ok(model)

    def get_by_id(self, entity_id: str) -> Result[T, str]:
        if entity_id not in self._storage:
            return Err(f"Entity with id {entity_id} not found")
        return Ok(self._storage[entity_id])

    def delete_by_id(self, entity_id: str) -> Result[bool, str]:
        with self._lock:
            if entity_id not in self._storage:
                return Err(f"Entity with id {entity_id} not found")
            del self._storage[entity_id]
            return Ok(True)

    def get_all(self) -> Result[List[T], str]:
        return Ok(list(self._storage.values()))
