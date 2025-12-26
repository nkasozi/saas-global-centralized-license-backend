from result import Err, Ok

from src.core.models.activation import Activation
from src.infrastructure.persistence.file_based_db.file_repository import FileRepository


class ActivationRepository(FileRepository[Activation]):
    def __init__(self):
        super().__init__("data/activations.json", Activation)

    def get_by_license_key_id(self, license_key_id: str):
        all_activations_result = self.get_all()
        if all_activations_result.is_err():
            return all_activations_result

        matching = [a for a in all_activations_result.ok_value if a.license_key_id == license_key_id]

        return Ok(matching)

    def get_by_license_key_id_and_instance_id(self, license_key_id: str, instance_id: str):
        all_activations_result = self.get_all()
        if all_activations_result.is_err():
            return all_activations_result

        matching = [
            a
            for a in all_activations_result.ok_value
            if a.license_key_id == license_key_id and a.instance_id == instance_id
        ]

        if not matching:
            return Err("Activation not found")

        return Ok(matching[0])
