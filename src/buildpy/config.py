from pathlib import Path
import attr, attrs
attr.s, attr.ib = attrs.define, attrs.field


# TODO: GlobalConfig -> Config, where
#   GlobalConfig: main config file location etc.
#   Config: per-repo-settings

@attr.s
class Config:
	config_root: Path = Path.home()/'build.py'
	pkgbuild_root: Path = Path.home()/'pkgbuild'

	repo_name: str = 'custom'
	makepkg_conf: Path = config_root/'makepkg.conf'
	pacman_conf: Path = config_root/'pacman.conf'
