from .base import PackageProvider
from .local import LocalPackageProvider

_PROVIDERS = (
	LocalPackageProvider(),
)
_REGISTRY = { type(p): p for p in _PROVIDERS }
