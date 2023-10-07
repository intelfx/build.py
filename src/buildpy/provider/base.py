from typing import (
	TYPE_CHECKING,
	ClassVar,
	Self,
)
from abc import ABC, abstractmethod

if TYPE_CHECKING:
	from buildpy.context import AppContext


class PackageProvider(ABC):
	id: ClassVar[str]

	@abstractmethod
	def __init__(self, _: 'AppContext'):
		...

	@classmethod
	def get(cls, ctx: 'AppContext') -> Self:
		return ctx.providers[cls]
