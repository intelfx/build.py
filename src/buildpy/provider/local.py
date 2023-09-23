from typing import (
	ClassVar,
)

from buildpy.package import Pkgbase, Pkgname
from .base import PackageProvider


class LocalPackageProvider(PackageProvider):
	id: ClassVar[str] = 'local'
	pkgbases: list[Pkgbase]
	pkgnames: list[Pkgname]
	by_pkgname: dict[str, list[Pkgname]]
	by_provides: dict[str, list[Pkgname]]

	def __init__(self):
		self.pkgbases = []
		self.pkgnames = []
		self.by_pkgname = {}
		self.by_provides = {}
