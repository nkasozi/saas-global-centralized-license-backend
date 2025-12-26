from typing import List

from result import Err, Ok, Result

from infrastructure.persistence.in_memory_db.in_memory_repository import InMemoryRepository
from src.core.models.activation import Activation


class ActivationRepository(InMemoryRepository[Activation]):
    def get_by_license_key_id(self, license_key_id: str) -> Result[List[Activation], str]:
        activations_for_key = [a for a in self._storage.values() if a.license_key_id == license_key_id]
        return Ok(activations_for_key)

    def get_by_instance_id(self, instance_id: str) -> Result[List[Activation], str]:
        activations_for_instance = [a for a in self._storage.values() if a.instance_id == instance_id]
        return Ok(activations_for_instance)

    def get_by_license_key_id_and_instance_id(self, license_key_id: str, instance_id: str) -> Result[Activation, str]:
        matching_activations = [
            a for a in self._storage.values() if a.license_key_id == license_key_id and a.instance_id == instance_id
        ]

        if not matching_activations:
            return Err(f"Activation not found for license key {license_key_id} and instance {instance_id}")

        return Ok(matching_activations[0])
