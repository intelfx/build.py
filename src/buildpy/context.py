import contextlib
import tempfile
from typing import (
	TYPE_CHECKING,
	TypeVar,
	Any,
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
	_tmpdirs: dict[Any, tempfile.TemporaryDirectory] = attr.ib(factory=dict)

	def tmpdir(self, tag=None, suffix=None, prefix=None, dir=None, ignore_cleanup_errors=False) \
			-> tempfile.TemporaryDirectory:
		if tag is not None:
			try:
				return self._tmpdirs[tag]
			except KeyError:
				pass
		r = self._push_context(
			tempfile.TemporaryDirectory(
				suffix=suffix,
				prefix=prefix,
				dir=dir,
				ignore_cleanup_errors=ignore_cleanup_errors,
			)
		)
		if tag is not None:
			self._tmpdirs[tag] = r
		return r

	def _push_context(self, obj: T) -> T:
		self._stack.enter_context(obj)
		return obj

	def _with_context(self, obj: contextlib.AbstractContextManager[T]) -> T:
		return self._stack.enter_context(obj)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return self._stack.__exit__(exc_type, exc_val, exc_tb)
