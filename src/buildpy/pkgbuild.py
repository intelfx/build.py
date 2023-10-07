import enum
import subprocess
from pathlib import Path
from typing import (
	TYPE_CHECKING,
	Self,
)

import attr, attrs
attr.s, attr.ib = attrs.define, attrs.field

import buildpy.util
from buildpy.config import Config
if TYPE_CHECKING:
	from buildpy.srcinfo import SRCINFO


@attr.s
class PKGBUILD:
	class Error(RuntimeError):
		def __init__(self, pkgbuild: 'PKGBUILD', *args):
			self.pkgbuild = pkgbuild
			super().__init__(*args)

		def __str__(self):
			return f'{self.pkgbuild}: {super().__str__()}'

	class State(enum.Flag):
		Unparsed = 0
		NameLoaded = enum.auto()
		PkgbuildLoaded = enum.auto()
		UpstreamLoaded = enum.auto()
	state: State
	base_dir: Path
	pkgbuild_file: Path
	# TODO: per-pkgbase config
	# TODO: git dir

	pkgbase: str = None
	pkgname: list[str] = None
	srcinfo: 'SRCINFO' = None

	def __str__(self):
		return f'PKGBUILD({self.pkgbuild_file})'

	def r4ise(self, *args):
		raise self.Error(self, *args)

	@classmethod
	def from_path(cls, base_dir: Path, pkgbuild_file: Path) -> Self:
		return cls(
			state=cls.State.Unparsed,
			base_dir=base_dir,
			pkgbuild_file=pkgbuild_file,
		)

	@classmethod
	def from_config(cls, config_file: Path) -> Self:
		raise NotImplementedError()

	def _makepkg_args(self, args: list[str], *, config: Config) -> list[str]:
		cmdline: list[str] = [ 'makepkg' ]
		if config.makepkg_conf:
			cmdline += [ '--config', config.makepkg_conf ]
		if self.pkgbuild_file.name != 'PKGBUILD':
			# makepkg must be called from pkgbuild directory
			# don't bother with computing relative path
			cmdline += [ '-p', self.pkgbuild_file.name ]
		cmdline += args
		return cmdline

	def run_makepkg(self, args: list[str], *, config: Config, **kwargs) \
			-> subprocess.CompletedProcess[str]:
		return subprocess.run(
			args=self._makepkg_args(args, config=config),
			cwd=self.pkgbuild_file.parent,
			check=True,
			text=True,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			**kwargs,
		)

	def pipe_makepkg(self, args: list[str], *, config: Config, **kwargs) \
			-> subprocess.Popen[str]:
		return buildpy.util.Popen(
			args=self._makepkg_args(args, config=config),
			cwd=self.pkgbuild_file.parent,
			check=True,
			text=True,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			**kwargs,
		)

	def has_git(self) -> bool:
		# TODO: use git dir
		git_dir = self.base_dir/'.git'
		return git_dir.exists()

	def run_git(self, args: list[str], *, config: Config, **kwargs) \
			-> subprocess.CompletedProcess[str]:
		if not self.has_git():
			self.r4ise(f'run_git() in a non-git-tracked package')
		# TODO: use git dir
		git_root = self.base_dir
		cmdline: list[str] = [ 'git' ]
		cmdline += args

		return subprocess.run(
			args=cmdline,
			cwd=git_root,
			check=True,
			text=True,
			**kwargs,
		)
