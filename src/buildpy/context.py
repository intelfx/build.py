import attr, attrs

from buildpy.config import Config

attr.s, attr.ib = attrs.define, attrs.field


@attr.s
class AppContext:
	config: Config
