import collections
import typing
from collections import abc
import re
from typing import (
	TYPE_CHECKING,
	TypeAlias,
)

import attr, attrs
attr.s, attr.ib = attrs.define, attrs.field

from buildpy.config import Config
if TYPE_CHECKING:
	from buildpy.pkgbuild import PKGBUILD


# no tagged unions in python :-(
SrcinfoSectionHeader = collections.namedtuple('SrcinfoSectionHeader', ['type', 'name'])
SrcinfoKey: TypeAlias = str|tuple[str, str]
SrcinfoValue: TypeAlias = str|list[str]
SrcinfoSection: TypeAlias = dict[SrcinfoKey, SrcinfoValue]


@attr.s
class SRCINFO:
	# section of section headers
	headers: SrcinfoSection
	# contents of actual sections
	sections: dict[SrcinfoSectionHeader, SrcinfoSection]

	@classmethod
	def from_lines(cls, srcinfo_lines: abc.Iterable[str], pkgbuild: 'PKGBUILD'):
		section_keys = (
			'pkgbase',
			'pkgname',
		)
		pkgbase_keys = (
			'pkgver',
			'pkgrel',
			'epoch',
		)
		single_keys = (
			'pkgdesc',
			'url',
			'install',
			'changelog',
		)
		list_keys = (
			'arch',
			'groups',
			'license',
			'noextract',
			'options',
			'backup',
			'validpgpkeys',
		)
		arch_keys = (
			'source',
			'depends',
			'checkdepends',
			'makedepends',
			'optdepends',
			'provides',
			'conflicts',
			'replaces',
			'md5sums',
			'sha1sums',
			'sha224sums',
			'sha256sums',
			'sha384sums',
			'sha512sums',
		)

		# section of section headers
		headers: SrcinfoSection = dict()
		# contents of sections
		sections: dict[SrcinfoSectionHeader, SrcinfoSection] = dict()
		pkgbase_header: SrcinfoSectionHeader = None
		pkgbase_section: SrcinfoSection = None
		cur_header: SrcinfoSectionHeader = None
		cur_section: SrcinfoSection = None

		def get_value(section: SrcinfoSection, key: SrcinfoKey):
			try:
				return section[key]
			except KeyError:
				return pkgbase_section[key]

		def set_list_value(section: SrcinfoSection, key: SrcinfoKey, value: SrcinfoValue):
			# special case: single empty list item overrides pkgbase-level list
			# with an empty one
			if not value and key not in section:
				section[key] = list()
			else:
				section.setdefault(key, list()).append(value)

		for line in srcinfo_lines:
			# skip comments
			if re.match(r'^\s*(#|$)', line):
				pass
			elif m := re.fullmatch(r'\s*([a-zA-Z0-9_]+)\s*=\s*(.*)', line):
				key, value = m.group(1), m.group(2)
				assert key.strip() == key
				assert value.strip() == value

				if key in section_keys:
					cur_header = SrcinfoSectionHeader(key, value)
					if cur_header in sections:
						pkgbuild.r4ise(f'bad .SRCINFO: duplicate section {cur_header}')
					cur_section = sections[cur_header] = dict()

					if key == 'pkgbase':
						if pkgbase_header is not None:
							pkgbuild.r4ise(f'bad .SRCINFO: multiple pkgbase sections: {pkgbase_header} and {cur_header}')
						pkgbase_header, pkgbase_section = cur_header, cur_section

					# save section header as a key
					if key == 'pkgbase':
						headers[key] = value
					else:
						set_list_value(headers, key, value)
				else:
					if cur_header is None or cur_section is None:
						pkgbuild.r4ise(f'bad .SRCINFO: non-section key {key} before any section')
					if key in pkgbase_keys and cur_header.type != 'pkgbase':
						pkgbuild.r4ise(f'bad .SRCINFO: pkgbase-only key {key} in section {cur_header}')

					if key in pkgbase_keys or key in single_keys:
						if key in cur_section:
							pkgbuild.r4ise(f'bad .SRCINFO: non-unique key {key} in section {cur_header}')
						cur_section[key] = value
					elif key in list_keys or key in arch_keys:
						set_list_value(cur_section, key, value)
					elif ((arch_key := key.split('_', maxsplit=1))
					      and len(arch_key) == 2
					      and arch_key[0] in arch_keys
					      and arch_key[1] in get_value(cur_section, 'arch')):
						# FIXME: per-arch key handling
						set_list_value(cur_section, key, value)
					else:
						pkgbuild.r4ise(f'bad .SRCINFO: unknown key {key}')
			else:
				pkgbuild.r4ise(f'bad line in .SRCINFO: {line}')

		return cls(headers=headers, sections=sections)

	@classmethod
	def from_file(cls, srcinfo_file: typing.TextIO, pkgbuild: 'PKGBUILD'):
		return cls.from_lines(srcinfo_file.readlines(), pkgbuild=pkgbuild)

	@classmethod
	def from_pkgbuild(cls, pkgbuild: 'PKGBUILD', config: Config):
		srcinfo_file = pkgbuild.pkgbuild_file.parent/'.SRCINFO'
		if srcinfo_file.exists() and srcinfo_file.stat().st_mtime >= pkgbuild.pkgbuild_file.stat().st_mtime:
			with srcinfo_file.open('r') as f:
				text = f.read()
		else:
			srcinfo = pkgbuild.run_makepkg([ '--printsrcinfo' ], config=config)
			text = srcinfo.stdout
			with srcinfo_file.open('w') as f:
				f.write(text)

		return cls.from_lines(text.splitlines(), pkgbuild=pkgbuild)
