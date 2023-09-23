from .base import PackageProvider
from .local import LocalPackageProvider

_PROVIDERS = (
)
_REGISTRY = { type(p): p for p in _PROVIDERS }
