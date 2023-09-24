from .base import PackageProvider
from .local import LocalPackageProvider
from .aur import AURPackageProvider

_PROVIDERS = (
	LocalPackageProvider(),
	AURPackageProvider(),
)
_REGISTRY = { type(p): p for p in _PROVIDERS }
