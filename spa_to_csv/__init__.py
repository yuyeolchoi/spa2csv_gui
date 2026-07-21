"""Thermo OMNIC SPA to CSV converter."""

from .converter import convert_spa_to_csv
from .parser import SpaParseError, parse_spa

__version__ = "0.1.0"
AUTHOR = "yuyeolchoi"
GITHUB_URL = "https://github.com/yuyeolchoi"

__all__ = [
    "SpaParseError",
    "parse_spa",
    "convert_spa_to_csv",
    "__version__",
    "AUTHOR",
    "GITHUB_URL",
]
