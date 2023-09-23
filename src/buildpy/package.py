from typing import (
	Any,
)

import attr, attrs
attr.s, attr.ib = attrs.define, attrs.field


@attr.s
class Pkgbase:
	pkgbase: str
	version: str
	pkgnames: 'list[Pkgname]'
	depends: 'list[Pkgname|str]'
	makedepends: 'list[Pkgname|str]'
	optdepends: 'list[Pkgname|str]'
	provider: Any


@attr.s
class Pkgname:
	pkgbase: Pkgbase
	pkgname: str
	depends: 'list[Pkgname|str]'
	makedepends: 'list[Pkgname|str]'
	optdepends: 'list[Pkgname|str]'
	provides: 'list[str]'
