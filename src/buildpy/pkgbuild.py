import enum
import subprocess
from pathlib import Path

import attr, attrs
attr.s, attr.ib = attrs.define, attrs.field

from buildpy.config import Config


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

	pkgbase: str = None
	pkgname: list[str] = None

	def __str__(self):
		return f'PKGBUILD({self.pkgbuild_file})'

	def r4ise(self, *args):
		raise self.Error(self, *args)

	@classmethod
	def from_path(cls, base_dir: Path, pkgbuild_file: Path):
		return cls(
			state=cls.State.Unparsed,
			base_dir=base_dir,
			pkgbuild_file=pkgbuild_file,
		)

	@classmethod
	def from_config(cls, config_file: Path):
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
		return subprocess.Popen(
			args=self._makepkg_args(args, config=config),
			cwd=self.pkgbuild_file.parent,
			text=True,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			**kwargs,
		)
