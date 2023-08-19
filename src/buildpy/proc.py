import os
from pathlib import Path

from buildpy.config import Config
from buildpy.pkgbuild import PKGBUILD


def find_pkgbuilds(config: Config) -> list[PKGBUILD]:
	for path, dirs, files in os.walk(config.pkgbuild_root, onerror=lambda e: exec('raise e')):
		path = Path(path)
		# 1. trivial case: if PKGBUILD exists -> load it
		if 'PKGBUILD' in files:
			yield PKGBUILD.from_path(path, path/'PKGBUILD')
			dirs[:] = []
		# 2. asp-style checkouts: if trunk/PKGBUILD exists -> load it and do not traverse further
		#    (this will necessarily happen before (1) due to topdown=True)
		elif 'trunk' in dirs and (path/'trunk'/'PKGBUILD').is_file():
			yield PKGBUILD.from_path(path, path/'trunk'/'PKGBUILD')
			dirs[:] = []
		# 3. TODO: per-pkgbase config: if exists -> load indicated PKGBUILD, do not traverse further
		# 4. TODO: multiple pkgbase per git repo: remember and save git dir
