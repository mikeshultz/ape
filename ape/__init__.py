from importlib.metadata import version, PackageNotFoundError

from . import _setup  # NOTE: Do this before anything else

try:
    __version__ = version("ape")
except PackageNotFoundError:
    # package is not installed
    pass