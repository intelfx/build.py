import contextlib
from typing import (
	TYPE_CHECKING,
	TypeVar,
)
import attr, attrs

from buildpy.config import Config
if TYPE_CHECKING:
	from buildpy.provider import PackageProvider

attr.s, attr.ib = attrs.define, attrs.field

Tp = TypeVar('Tp', bound='PackageProvider')
T = TypeVar('T')


@attr.s
class AppContext:
	config: Config
	providers: dict[type[Tp], Tp] = attr.ib(factory=dict)
	_stack: contextlib.ExitStack = attr.ib(factory=contextlib.ExitStack)

	def _push_context(self, obj: T) -> T:
		self._stack.enter_context(obj)
		return obj

	def _with_context(self, obj: contextlib.AbstractContextManager[T]) -> T:
		return self._stack.enter_context(obj)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return self._stack.__exit__(exc_type, exc_val, exc_tb)
