from collections import abc
from typing import (
	TypeAlias,
	ClassVar,
	Optional,
)
import attr, attrs
import cattrs
import cattrs.strategies
import cattrs.preconf.json
import requests

import buildpy.util
from buildpy.package import Pkgbase, Pkgname
from .base import PackageProvider

attr.s, attr.ib = attrs.define, attrs.field


@attr.s
class SearchResult:
	ID: int
	Name: str
	PackageBaseID: int
	PackageBase: str
	Version: str
	Description: str
	URL: str
	NumVotes: int
	Popularity: int
	OutOfDate: bool
	Maintainer: str
	FirstSubmitted: str
	LastModified: str
	URLPath: str

@attr.s(field_transformer=buildpy.util.factorize)
class InfoResult(SearchResult):
	License: str
	Depends: list[str] = []
	MakeDepends: list[str] = []
	OptDepends: list[str] = []
	CheckDepends: list[str] = []
	Conflicts: list[str] = []
	Provides: list[str] = []
	Replaces: list[str] = []
	Groups: list[str] = []
	Keywords: list[str] = []

@attr.s
class BaseResponse:
	converter: ClassVar[cattrs.preconf.json.JsonConverter]
	type: ClassVar[str]
	version: int
	resultcount: int

@attr.s
class ErrorResponse(BaseResponse):
	type: ClassVar[str] = 'error'
	results: list
	error: str

@attr.s
class SearchResponse(BaseResponse):
	type: ClassVar[str] = 'search'
	results: list[SearchResult]

@attr.s
class InfoResponse(BaseResponse):
	type: ClassVar[str] = 'multiinfo'
	results: list[InfoResult]

Response: TypeAlias = ErrorResponse|SearchResponse|InfoResponse

BaseResponse.converter = cattrs.preconf.json.make_converter()
cattrs.strategies.configure_tagged_union(
	Response,
	BaseResponse.converter,
	tag_generator=lambda t: t.type,
	tag_name='type',
)


class AURPackageProvider(PackageProvider):
	class Error(RuntimeError):
		url: Optional[str] = None

		def __init__(
			self,
			*args,
			req: Optional[requests.Request] = None,
			resp: Optional[requests.Response] = None,
		):
			super().__init__(*args)
			if resp is not None:
				self.add_note(resp.text)
				if req is None:
					req = resp.request
			if req is not None:
				self.url = req.url.removeprefix(AURPackageProvider.base_url)

		def __str__(self):
			s = 'AUR Error'
			if self.url:
				s += f': {self.url}'
			if msg := super().__str__():
				s += f': {msg}'
			return s

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

	def load_packages(self, pkgnames: list[str]):
		# step 1: direct lookup by pkgname
		direct_targets = set(pkgnames) - self.by_pkgname.keys()
		direct_pkgs = [
			self._load_result(r)
			for r
			in self._aur_info(list(direct_targets))
		]
		direct_names = { p.pkgname for p in direct_pkgs }
		direct_missing = direct_targets - direct_names

		# step 2: lookup by provides
		virtual_targets = direct_missing - self.by_provides.keys()
		virtual_pkgs = [
			self._load_result(r)
			for name in virtual_targets
			for r in self._aur_search(field='provides', query=name)
		]
		# search only gives partial results; fully load them to get provided names
		# TODO: somehow inject the searched-for provided name into the corresponding Pkgnames
		#       this way we can avoid (or delay) fully loading Pkgnames but still resolve the required names
		virtual_pkgs = [
			self._load_result(r)
			for r in self._aur_info([ p.pkgname for p in virtual_pkgs ])
		]
		virtual_names = { name for p in virtual_pkgs for name in p.provides }
		virtual_missing = virtual_targets - virtual_names

	def _load_result(self, arg: SearchResult|InfoResult) -> Pkgname:
		# lookup pkgbase and pkgname
		pkgname = self.pkgnames.get(arg.ID)
		pkgbase = pkgname.pkgbase if pkgname is not None else self.pkgbases.get(arg.PackageBaseID)

		# create missing pkgbase
		if pkgbase is None:
			pkgbase = Pkgbase(
				pkgbase=arg.PackageBase,
				version=arg.Version,
				pkgnames=[],
				depends=[],
				makedepends=[],
				optdepends=[],
				provider=self,
				uptodate=True,  # AUR does not provide pkgbase info, thus always True
			)
			self.pkgbases[arg.PackageBaseID] = pkgbase

		# create missing pkgname
		if pkgname is None:
			pkgname = Pkgname(
				pkgbase=pkgbase,
				pkgname=arg.Name,
				depends=[],
				makedepends=[],
				optdepends=[],
				provides=[],
				uptodate=False,
			)
			pkgbase.pkgnames.append(pkgname)
			self.pkgnames[arg.ID] = pkgname
			# update lookup dictionaries, step 1
			self.by_pkgname.setdefault(pkgname.pkgname, []).append(pkgname)

		# extend pkgname if we got a full result
		if not pkgname.uptodate and isinstance(arg, InfoResult):
			pkgname.depends = arg.Depends
			pkgname.makedepends = arg.MakeDepends
			pkgname.optdepends = arg.OptDepends
			pkgname.provides = arg.Provides
			pkgname.uptodate = True
			# update lookup dictionaries, step 2
			for name in pkgname.provides:
				self.by_provides.setdefault(name, []).append(pkgname)

		return pkgname

	def _aur_search(self, field: str, query: str) -> list[SearchResult]:
		resp = self._aur_query(
			method='GET',
			url=f'/rpc/v5/search/{query}',
			params={ 'by': field },
		)
		if not isinstance(resp, SearchResponse):
			raise self.Error(f'Invalid response type: {resp}')
		return resp.results

	def _aur_info(self, pkgnames: abc.Iterable[str]) -> list[InfoResult]:
		resp = self._aur_query(
			method='POST',
			url='/rpc/v5/info',
			data={ 'arg[]': pkgnames },
		)
		if not isinstance(resp, InfoResponse):
			raise self.Error(f'Invalid response type: {resp}')
		return resp.results

	def _aur_query(
		self,
		method: str,
		url: str,
		params: Optional[dict[str, str]] = None,
		data: Optional = None,
	) -> Response:
		resp = None
		try:
			resp = requests.request(
				method=method,
				url=self.base_url + url,
				params=params,
				data=data,
				allow_redirects=False,
			)
			resp.raise_for_status()
			resp_obj: Response = BaseResponse.converter.structure(resp.json(), Response)
			if resp_obj.version != 5:
				raise self.Error(f'Invalid response version', resp=resp)
			if isinstance(resp_obj, ErrorResponse):
				raise self.Error(f'RPC error: {resp_obj.error}', resp=resp)
			return resp_obj
		except self.Error:
			raise
		except requests.HTTPError as e:
			raise self.Error(e, req=e.request, resp=e.response) from e
		except Exception as e:
			raise self.Error(e, resp=resp) from e
