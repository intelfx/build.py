from typing import (
	ClassVar,
	Self,
)
from abc import ABC, abstractmethod


class PackageProvider(ABC):
	id: ClassVar[str]

	@classmethod
	def get(cls) -> Self:
		from . import _REGISTRY
		return _REGISTRY[cls]  # noqa
