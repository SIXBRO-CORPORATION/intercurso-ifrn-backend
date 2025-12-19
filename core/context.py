from typing import Any, Optional, Type, TypeVar

T = TypeVar("T")


class Context:
    def __init__(self, data: Any = None):
        self._storage: dict[str, Any] = {}
        if data is not None:
            self._storage["data"] = data

    def get_data(self, cls: Type[T]) -> Optional[T]:
        data = self._storage.get("data")
        if isinstance(data, cls):
            return data
        return None

    def set_data(self, data: Any) -> None:
        self._storage["data"] = data

    def put_property(self, key: str, value: Any) -> None:
        self._storage[key] = value

    def get_property(self, key: str, cls: Type[T]) -> Optional[T]:
        value = self._storage.get(key)
        if isinstance(value, cls):
            return value
        return None

    def get(self, key: str) -> Any:
        return self._storage.get(key)
