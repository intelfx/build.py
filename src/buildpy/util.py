import contextlib
import re
import tempfile
import typing
from pathlib import Path

# importing this file; for consistency
from buildpy import util


def with_newline(arg: str) -> str:
	if not arg.endswith('\n'):
		return arg + '\n'
	return arg


@contextlib.contextmanager
def pacman_conf_prepend_repo(pacman_conf: Path, repo_name: str, repo_section: str) -> typing.TextIO:
	with pacman_conf.open('r') as f:
		text = f.read()

	repo_text = f"[{repo_name}]\n{repo_section}"

	if re.search(fr'^\[{repo_name}\]$', text, flags=re.MULTILINE):
		raise RuntimeError(f"pacman.conf template {pacman_conf} already contains [{repo_name}]")

	for m in re.finditer(r'^#?\[(.+)\]$', text, flags=re.MULTILINE):
		if m.group(1) != "options":
			prefix, suffix = text[:m.start()], text[m.start():]
			text = f"{prefix}{util.with_newline(repo_text)}\n{suffix}"
			break
	else:
		text = f"{util.with_newline(text)}\n{repo_text}"

	with tempfile.NamedTemporaryFile(mode="w+", prefix='pacman', suffix='.conf') as f:
		f.write(text)
		f.seek(0)
		yield f
