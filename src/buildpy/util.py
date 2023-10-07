import copy
import functools
import re
import subprocess
import tempfile
import typing
import attrs
from collections import abc
from pathlib import Path

from configupdater import ConfigUpdater

# importing this file; for consistency
from buildpy import util


def _factorize_one(field: attrs.Attribute) -> attrs.Attribute:
	# `abc.Collection` matches all normal "footguns" (`list`, `set`, `dict`) but also immutable objects
	# that also happen to be sized and iterable (`str`, `bytes`). Tuples are also do not need to be transformed.
	# To avoid this, also perform a negative check for `abc.Hashable` because any hashable object is immutable
	# and therefore won't be a footgun in practice.
	if isinstance(field.default, abc.Collection) and not isinstance(field.default, abc.Hashable):
		if len(field.default) == 0:
			# if it's an empty container, directly use container's type constructor
			return field.evolve(default=attrs.Factory(type(field.default)))
		else:
			# if it's a non-empty container, we have to copy it
			return field.evolve(default=attrs.Factory(lambda: copy.copy(field.default)))
	return field


def factorize(cls: type, fields: list[attrs.Attribute]) -> list[attrs.Attribute]:
	"""
	A hook for `attrs.define(field_transformer=...)` that converts containers into factories in default field values
	(thus preventing footguns)::

		@attrs.define(field_transformer=factorize)
		class Foo:
			field: list[str] = []  # not a footgun

	"""
	return [ _factorize_one(f) for f in fields ]


def with_newline(arg: str) -> str:
	if not arg.endswith('\n'):
		return arg + '\n'
	return arg


def pacman_conf_remove_repo(dir: Path, pacman_conf: Path, repos: abc.Sequence[str]) \
		-> Path:
	conf = ConfigUpdater(allow_no_value=True)
	conf.read(pacman_conf)
	for r in repos:
		conf.remove_section(r)

	with tempfile.NamedTemporaryFile(mode='w', dir=dir, prefix='pacman', suffix='.conf', delete=False) as f:
		conf.write(f)
	return Path(f.name)


def pacman_conf_prepend_repo2(pacman_conf: Path, repo_name: str, repo_section: str) -> typing.TextIO:
	repo_text = f'[{repo_name}]\n{repo_section}'
	section = ConfigUpdater(allow_no_value=True)
	section.read_string(repo_text)

	conf = ConfigUpdater(allow_no_value=True)
	conf.read(pacman_conf)
	conf['options'].add_after.section(section[repo_name].detach()).space(2)

	f = tempfile.NamedTemporaryFile(mode='w+', prefix='pacman', suffix='.conf')
	conf.write(f)
	f.seek(0)
	return f


def pacman_conf_prepend_repo(pacman_conf: Path, repo_name: str, repo_section: str) -> typing.TextIO:
	with pacman_conf.open('r') as f:
		text = f.read()

	repo_text = f'[{repo_name}]\n{repo_section}'

	if re.search(fr'^\[{repo_name}\]$', text, flags=re.MULTILINE):
		raise RuntimeError(f'pacman.conf template {pacman_conf} already contains [{repo_name}]')

	for m in re.finditer(r'^#?\[(.+)\]$', text, flags=re.MULTILINE):
		if m.group(1) != 'options':
			prefix, suffix = text[:m.start()], text[m.start():]
			text = f'{prefix}{util.with_newline(repo_text)}\n{suffix}'
			break
	else:
		text = f'{util.with_newline(text)}\n{repo_text}'

	f = tempfile.NamedTemporaryFile(mode='w+', prefix='pacman', suffix='.conf')
	f.write(text)
	f.seek(0)
	return f


class Popen(subprocess.Popen):
	_check: bool

	@functools.wraps(subprocess.Popen.__init__)
	# explode commonly used parameters by hand to aid PyCharm code completion
	def __init__(
			self, args, *, stdin=None, stdout=None, stderr=None, cwd=None,
			env=None, text=None, encoding=None, errors=None, check=False, **kwargs
	):
		super().__init__(
			args=args, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd,
			env=env, text=text, encoding=encoding, errors=errors, **kwargs,
		)
		self._check = check

	def __exit__(self, exc_type, exc_val, exc_tb):
		try:
			super().__exit__(exc_type, exc_val, exc_tb)  # will wait()
		finally:
			if self._check:
				assert self.returncode is not None
				if self.returncode != 0:
					raise subprocess.CalledProcessError(self.returncode, self.args)
