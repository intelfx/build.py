from collections import abc
import contextlib
from pathlib import Path
import tempfile

import pytest


def is_bytes(arg: str|bytes) -> bool:
	# check if contents is bytes-like or str-like
	try:
		with memoryview(arg):
			return True
	except TypeError:
		return False


@pytest.fixture
def tmp_file(tmp_path) -> abc.Callable[..., Path]:
	def _make_file(contents: str|bytes, *, prefix: str = None, suffix: str = None) -> Path:
		mode = 'wb' if is_bytes(contents) else 'w'
		with tempfile.NamedTemporaryFile(
			mode=mode, prefix=prefix, suffix=suffix, dir=tmp_path, delete=False
		) as f:
			f.write(contents)
		return Path(f.name)
	return _make_file


@pytest.fixture
def tmp_fileobj(tmp_path) -> abc.Generator[Path, None, None]:
	@contextlib.contextmanager
	def _make_fileobj(contents: str|bytes, *, prefix: str = None, suffix: str = None) -> Path:
		mode = 'wb' if is_bytes(contents) else 'w'
		with tempfile.NamedTemporaryFile(
			mode=mode, prefix=prefix, suffix=suffix, dir=tmp_path
		) as f:
			f.write(contents)
			f.seek(0)
			yield f
	return _make_fileobj
