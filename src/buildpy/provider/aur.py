from typing import (
	ClassVar,
)
import requests

from buildpy.package import Pkgbase, Pkgname
from .base import PackageProvider


class AURPackageProvider(PackageProvider):
	id: ClassVar[str] = 'aur'
	base_url: ClassVar[str] = 'https://aur.archlinux.org'
	pkgbases: dict[int, Pkgbase]
	pkgnames: dict[int, Pkgname]
	by_pkgname: dict[str, list[Pkgname]]
	by_provides: dict[str, list[Pkgname]]

	def __init__(self):
		self.pkgbases = dict()
		self.pkgnames = dict()
		self.by_pkgname = dict()
		self.by_provides = dict()
