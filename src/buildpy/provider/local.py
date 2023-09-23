from typing import (
	ClassVar,
)

from buildpy.package import Pkgbase, Pkgname
from buildpy.pkgbuild import PKGBUILD
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

	def load_pkgbuilds(self, pkgbuilds: list[PKGBUILD]):
		for p in pkgbuilds:
			pkgbase_section = p.srcinfo.sections[('pkgbase', p.pkgbase)]
			assert len(p.pkgname) == 1 or 'provides' not in pkgbase_section

			if 'epoch' in pkgbase_section:
				version = f'{pkgbase_section["epoch"]}:{pkgbase_section["pkgver"]}-{pkgbase_section["pkgrel"]}'
			else:
				version = f'{pkgbase_section["pkgver"]}-{pkgbase_section["pkgrel"]}'

			pkgbase = Pkgbase(
				pkgbase=p.pkgbase,
				version=version,
				pkgnames=[],
				depends=pkgbase_section.get('depends', []),
				optdepends=pkgbase_section.get('optdepends', []),
				makedepends=pkgbase_section.get('makedepends', []),
				provider=self,
			)
			for n in p.pkgname:
				pkgname_section = p.srcinfo.sections[('pkgname', n)]
				pkgname = Pkgname(
					pkgbase=pkgbase,
					pkgname=n,
					depends=pkgname_section.get('depends', []),
					optdepends=pkgname_section.get('depends', []),
					makedepends=pkgname_section.get('makedepends', []),
					provides=pkgname_section.get('provides', pkgbase_section.get('provides', [])),
				)
				pkgbase.pkgnames.append(pkgname)

			self.pkgbases.append(pkgbase)
			self.pkgnames.extend(pkgbase.pkgnames)

		# update lookup dictionaries
		for pkgname in self.pkgnames:
			self.by_pkgname.setdefault(pkgname.pkgname, []).append(pkgname)
			for name in pkgname.provides:
				self.by_provides.setdefault(name, []).append(pkgname)
