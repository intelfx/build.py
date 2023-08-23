import functools
import re
import subprocess
import tempfile
import typing
from pathlib import Path

from configupdater import ConfigUpdater

# importing this file; for consistency
from buildpy import util


def with_newline(arg: str) -> str:
	if not arg.endswith('\n'):
		return arg + '\n'
	return arg


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
