from typing import (
	ClassVar,
	TypeVar,
)
from abc import ABC, abstractmethod

T = TypeVar('T')


class PackageProvider(ABC):
	id: ClassVar[str]

	@classmethod
	def get(cls: type[T]) -> T:
		from . import _REGISTRY
		return _REGISTRY[cls]  # noqa
