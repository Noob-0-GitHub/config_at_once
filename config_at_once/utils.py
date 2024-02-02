# noinspection PyUnresolvedReferences
import warnings
# noinspection PyUnresolvedReferences
from typing import Callable, Iterable, TypeVar, Type

T = TypeVar('T')

# Supported config file
INI_FILENAME_EXTENSIONS = [".ini", ".cfg", ".cg", ".conf", ".cnf", ".properties"]
JSON_FILENAME_EXTENSIONS = [".json"]
YAML_FILENAME_EXTENSIONS = [".yaml", ".yml"]
TOML_FILENAME_EXTENSIONS = [".toml"]
XML_FILENAME_EXTENSIONS = [".xml"]

SUPPORTED_FILE_EXTENSIONS = [
    INI_FILENAME_EXTENSIONS,
    JSON_FILENAME_EXTENSIONS,
    YAML_FILENAME_EXTENSIONS,
    TOML_FILENAME_EXTENSIONS,
    XML_FILENAME_EXTENSIONS
]
