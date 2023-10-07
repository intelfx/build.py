import enum
from pathlib import Path
import attr, attrs
attr.s, attr.ib = attrs.define, attrs.field


# TODO: GlobalConfig -> Config, where
#   GlobalConfig: main config file location etc.
#   Config: per-repo-settings

class Auth(enum.Enum):
	No = enum.auto()
	Fake = enum.auto()
	Real = enum.auto()


@attr.s
class Config:
	config_root: Path = Path('/etc/aurutils')
	pkgbuild_root: Path = Path.home()/'pkgbuild'

	repo_name: str = 'custom'
	makepkg_conf: Path = config_root/f'makepkg-{repo_name}.conf'
	pacman_conf: Path = config_root/f'pacman-{repo_name}.conf'

	auth_wrappers: dict[Auth, list[str]] = {
		Auth.Fake: [ 'unshare', '-Ur' ],
		Auth.Real: [ 'sudo' ],
	}

	def auth_wrapper(self, auth: Auth) -> list[str]:
		return self.auth_wrappers.get(auth, [])

	def with_auth_wrapper(self, auth: Auth, cmd: list[str]) -> list[str]:
		return self.auth_wrapper(auth) + cmd
