from typing import (
	TYPE_CHECKING,
	TypeVar,
)
import attr, attrs

from buildpy.config import Config
if TYPE_CHECKING:
	from buildpy.provider import PackageProvider

attr.s, attr.ib = attrs.define, attrs.field

Tp = TypeVar('Tp', bound='PackageProvider')


@attr.s
class AppContext:
	config: Config
	providers: dict[type[Tp], Tp] = attr.ib(factory=dict)
