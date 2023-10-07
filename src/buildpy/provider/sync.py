import tempfile
from collections import abc
from pathlib import Path
import subprocess
from typing import (
	TYPE_CHECKING,
	TypeAlias,
	ClassVar,
	Optional,
)
import attr, attrs
import cattrs
import cattrs.strategies
import cattrs.preconf.json
import requests

import buildpy.util
from buildpy.config import Config, Auth
from buildpy.package import Pkgbase, Pkgname
from .base import PackageProvider
if TYPE_CHECKING:
	from buildpy.context import AppContext

attr.s, attr.ib = attrs.define, attrs.field


class SyncPackageProvider(PackageProvider):
	id: ClassVar[str] = 'sync'
	work_dir: Path
	db_dir: Path
	pacman_conf: Path
	_uptodate: bool

	def __init__(self, ctx: 'AppContext', without_custom=True):
		self.work_dir = Path(ctx.tmpdir('SyncPackageProvider').name)

		self.db_dir = self.work_dir/'db'
		self.db_dir.mkdir()

		if without_custom:
			self.pacman_conf = buildpy.util.pacman_conf_remove_repo(
				dir=self.work_dir,
				pacman_conf=ctx.config.pacman_conf,
				repos=[ctx.config.repo_name],
			)
		else:
			self.pacman_conf = ctx.config.pacman_conf

		self._uptodate = False

	def update(self, config: Config):
		if self._uptodate:
			return
		self.run_pacman([ '-Sy' ], auth=Auth.Fake, config=config)

	def _pacman_args(self, args: list[str], *, auth: Auth, config: Config) -> list[str]:
		cmdline: list[str] = [ 'pacman' ]
		if self.db_dir:
			cmdline += [ '--dbpath', self.db_dir ]
		if self.pacman_conf:
			cmdline += [ '--config', self.pacman_conf ]
		cmdline += [ '--noconfirm' ]
		cmdline += args
		return config.with_auth_wrapper(auth, cmdline)

	def run_pacman(self, args: list[str], *, auth: Auth, config: Config, **kwargs) \
			-> subprocess.CompletedProcess[str]:
		pacman_kwargs = {
			'stdin': subprocess.DEVNULL,
		}
		pacman_kwargs.update(kwargs)
		return subprocess.run(
			args=self._pacman_args(args, auth=auth, config=config),
			check=True,
			text=True,
			**pacman_kwargs,
		)

	def pipe_pacman(self, args: list[str], *, auth: Auth, config: Config, **kwargs) \
			-> subprocess.Popen[str]:
		pacman_kwargs = {
			'stdin': subprocess.DEVNULL,
			'stdout': subprocess.PIPE,
		}
		pacman_kwargs.update(kwargs)
		return buildpy.util.Popen(
			args=self._pacman_args(args, auth=auth, config=config),
			check=True,
			text=True,
			**pacman_kwargs,
		)
