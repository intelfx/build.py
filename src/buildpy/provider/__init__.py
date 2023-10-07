from buildpy.context import AppContext
from .base import PackageProvider
from .local import LocalPackageProvider
from .aur import AURPackageProvider

_PROVIDERS = (
	LocalPackageProvider,
	AURPackageProvider,
)


def setup(ctx: AppContext):
	ctx.providers.update({ T: T(ctx) for T in _PROVIDERS })
