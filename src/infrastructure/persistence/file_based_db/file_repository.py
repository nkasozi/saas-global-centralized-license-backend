import json
import os
from dataclasses import fields
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Generic, List, TypeVar

from result import Err, Ok, Result

from src.core.models.model import Model
from src.core.ports.repository_interface import RepositoryInterface

T = TypeVar("T", bound=Model)


class FileRepository(RepositoryInterface[T], Generic[T]):
    def __init__(self, file_path: str, model_class: type[T]):
        self.file_path = file_path
        self.model_class = model_class
        self._lock = Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_data(self) -> dict:
        with self._lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}

    def _save_data(self, data: dict) -> Result[bool, str]:
        with self._lock:
            try:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                return Ok(True)
            except IOError as e:
                return Err(f"Failed to save data: {str(e)}")

    def _convert_string_to_datetime(self, value):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return value
        return value

    def _get_field_type(self, field_name: str):
        try:
            for field in fields(self.model_class):
                if field.name == field_name:
                    return field.type
        except TypeError:
            pass

        all_annotations = {}
        for klass in reversed(self.model_class.__mro__):
            if hasattr(klass, "__annotations__"):
                all_annotations.update(klass.__annotations__)

        return all_annotations.get(field_name)

    def _convert_string_to_enum(self, value, field_name: str):
        if not isinstance(value, str) and not isinstance(value, list):
            return value

        field_type = self._get_field_type(field_name)
        if not field_type:
            return value

        if isinstance(value, list):
            try:
                origin = getattr(field_type, "__origin__", None)
                args = getattr(field_type, "__args__", None)
                if origin is list and args and len(args) > 0:
                    element_type = args[0]
                    if isinstance(element_type, type) and issubclass(element_type, Enum):
                        return [element_type(item) if isinstance(item, str) else item for item in value]
            except (TypeError, ValueError, KeyError, AttributeError):
                pass
            return value

        if isinstance(value, str):
            try:
                if isinstance(field_type, type) and issubclass(field_type, Enum):
                    converted = field_type(value)
                    return converted
            except (TypeError, ValueError, KeyError, AttributeError):
                pass

        return value

    def _deserialize_model(self, data: dict) -> T:
        converted_data = {}
        for key, value in data.items():
            converted_value = self._convert_string_to_datetime(value)
            converted_value = self._convert_string_to_enum(converted_value, key)
            converted_data[key] = converted_value

        try:
            return self.model_class(**converted_data)
        except (ValueError, TypeError, KeyError) as e:
            raise ValueError(
                f"Failed to instantiate {self.model_class.__name__} with data {converted_data}: {e}"
            ) from e

    def _serialize_model(self, model: T) -> dict:
        data = {}
        if hasattr(model, "__dict__"):
            data = model.__dict__.copy()
        else:
            data = vars(model).copy()

        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, list):
                data[key] = [item.value if isinstance(item, Enum) else item for item in value]

        return data

    def save(self, model: T) -> Result[T, str]:
        if not model.id or not model.id.strip():
            return Err("Model must have a valid ID before saving")

        data = self._load_data()
        data[model.id] = self._serialize_model(model)
        save_result = self._save_data(data)

        if save_result.is_err():
            return Err(save_result.err_value)

        return Ok(model)

    def get_by_id(self, entity_id: str) -> Result[T, str]:
        data = self._load_data()

        if entity_id not in data:
            return Err(f"Entity with id {entity_id} not found")

        try:
            model_data = data[entity_id]
            model = self._deserialize_model(model_data)
            return Ok(model)
        except ValueError as e:
            return Err(f"Failed to deserialize model: {str(e)}")

    def delete_by_id(self, entity_id: str) -> Result[bool, str]:
        data = self._load_data()

        if entity_id not in data:
            return Err(f"Entity with id {entity_id} not found")

        del data[entity_id]
        save_result = self._save_data(data)

        if save_result.is_err():
            return Err(save_result.err_value)

        return Ok(True)

    def get_all(self) -> Result[List[T], str]:
        data = self._load_data()

        try:
            models = [self._deserialize_model(model_data) for model_data in data.values()]
            return Ok(models)
        except ValueError as e:
            return Err(f"Failed to deserialize models: {str(e)}")
