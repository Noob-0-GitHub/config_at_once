import abc
import os.path

from .config_tree import ConfigTree
from .utils import *

_FuncT = TypeVar("_FuncT")


class AbcGroup(abc):
    """
    Abstract method:
        _build_local_config_tree
        save_to_dict
        load_from_dict

    Represents a group of configurations, aiding in the organization and management of related configurations.

    The Group class allows for the addition of classes to groups, making it easier to initialize
    configurations and apply them en masse. It interacts with the ConfigTree to provide
    serialization and deserialization of group configurations.

    Attributes:
        name: A string representing the name of the group.
        tree: A ConfigTree object that holds the configurations of the group.
        registered: A set that keeps track of the classes added to this group.
    """
    WARNING = True

    def __init__(self, filepath: str, name: str):
        """
        Initialize ConfigGroup.
        :param filepath: The saving filepath of the config group.
        :param name: Name of the group.
        """
        super().__init__()
        self.filepath = filepath
        self.name = name
        self.registered: set = set()
        self.tree: ConfigTree = ConfigTree(group=self)
        self._Template = type("Template", (self._Template,), {"group": self})

    @abc.abstractmethod
    def _build_config_tree(self, root: dict):
        pass

    @abc.abstractmethod
    def _build_local_config_tree(self, attr_name: str, _cls: Any, check_if_to_config: bool = True,
                                 treed_obj: (list, set) = None) -> (ConfigTree, None):
        """
        Build LocalTree.
        :param _cls:
        :param check_if_to_config:
        :return: ConfigTree or None.
        """
        pass

    def load(self):
        if os.path.exists(self.filepath):
            try:
                self.load_from_file(self.filepath)
            except Exception as e:
                if self.WARNING:
                    warnings.warn(f"load {self.filepath} error: {e}", RuntimeWarning)
                    self.save_to_file(self.filepath)
                else:
                    raise e
        else:
            self.save_to_file(self.filepath)

    @abc.abstractmethod
    def save_to_dict(self) -> None:
        pass

    @abc.abstractmethod
    def load_from_dict(self, config_dict: dict, root: dict) -> (ConfigTree, None):
        """
        Load config from dict.
        :param config_dict: Config dict.
        :param root: Config root, usually is globals() or __dict__.
        :return: ConfigTree or None.
        """
        self.tree = self.rebuild_tree(config_dict)
        for attr_name, attr_value in self.tree.items():
            if attr_name not in root:
                warnings.warn(f"{attr_name} no found in {root}", RuntimeWarning)
                root[attr_name] = attr_value
            if isinstance(attr_value, ConfigTree):
                self.apply(attr_value, root[attr_name])
            else:
                root[attr_name] = attr_value

    def save_to_file(self, path: str = None):
        if path is None:
            path = self.filepath
        filename_extension = os.path.splitext(path)[1]
        if filename_extension in [".ini", ".cfg", ".cg", ".conf", ".cnf", ".properties"]:
            self.save_to_ini(path)
        elif filename_extension in JSON_FILENAME_EXTENSIONS:
            self.save_to_json(path)
        elif filename_extension in YAML_FILENAME_EXTENSIONS:
            self.save_to_yaml(path)
        elif filename_extension in TOML_FILENAME_EXTENSIONS:
            self.save_to_toml(path)
        elif filename_extension in XML_FILENAME_EXTENSIONS:
            self.save_to_xml(path)
        else:
            raise ValueError(f"Unexpected file extension: {filename_extension}")

    def save_to_ini(self, path: str = None):
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read_dict(self.tree)
            with open(path, "w") as config_file:
                config.write(config_file)
        except ImportError:
            raise ImportError("The module configparser is not installed")

    def save_to_json(self, path: str = None):
        try:
            import json
            with open(path, "w") as f:
                json.dump(self.tree, f)
        except ImportError:
            raise ImportError("The module json is not installed")

    def save_to_yaml(self, path: str = None):
        try:
            import yaml
            with open(path, "w") as f:
                yaml.dump(self.tree, f)
        except ImportError:
            raise ImportError("The module yaml is not installed")

    def save_to_toml(self, path: str = None):
        try:
            import toml
            with open(path, "w") as f:
                toml.dump(self.tree, f)
        except ImportError:
            raise ImportError("The module toml is not installed")

    def save_to_xml(self, path: str = None):
        try:
            import xmltodict
            with open(path, "w") as f:
                xmltodict.unparse(self.tree, f)
        except ImportError:
            raise ImportError("The module xmltodict is not installed")

    def load_from_file(self, path: str = None):
        if path is None:
            path = self.filepath
        filename_extension = os.path.splitext(path)[1]
        if filename_extension in INI_FILENAME_EXTENSIONS:
            self.load_from_ini(path)
        elif filename_extension in JSON_FILENAME_EXTENSIONS:
            self.load_from_json(path)
        elif filename_extension in YAML_FILENAME_EXTENSIONS:
            self.load_from_yaml(path)
        elif filename_extension in TOML_FILENAME_EXTENSIONS:
            self.load_from_toml(path)
        elif filename_extension in XML_FILENAME_EXTENSIONS:
            self.load_from_xml(path)
        else:
            raise ValueError(f"Unexpected file extension: {filename_extension}")

    def load_from_ini(self, path: str = None):
        if path is None:
            path = self.filepath
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(path)
            self.load_from_dict(config, globals())
        except ImportError:
            raise ImportError("The module configparser is not installed")

    def load_from_json(self, path: str = None):
        if path is None:
            path = self.filepath
        try:
            import json
            with open(path, "r") as f:
                self.load_from_dict(json.load(f), globals())
        except ImportError:
            raise ImportError("The module json is not installed")

    def load_from_yaml(self, path: str = None):
        if path is None:
            path = self.filepath
        try:
            import yaml
            with open(path, "r") as f:
                self.load_from_dict(yaml.load(f, Loader=yaml.FullLoader), globals())
        except ImportError:
            raise ImportError("The module yaml is not installed")

    def load_from_toml(self, path: str = None):
        if path is None:
            path = self.filepath
        try:
            import toml
            with open(path, "r") as f:
                self.load_from_dict(toml.load(f), globals())
        except ImportError:
            raise ImportError("The module toml is not installed")

    def load_from_xml(self, path: str = None):
        if path is None:
            path = self.filepath
        try:
            import xmltodict
            with open(path, "r") as f:
                self.load_from_dict(xmltodict.parse(f), globals())
        except ImportError:
            raise ImportError("The module xmltodict is not installed")

    def rebuild_tree(self, config_dict: dict) -> ConfigTree:
        """
        Rebuild the ConfigTree from a dictionary.
        :param config_dict: Dictionary from which the ConfigTree needs to be rebuilt.
        :return: A new ConfigTree instance.
        """
        tree = ConfigTree(group=self)
        for k, v in config_dict.items():
            if isinstance(v, dict):
                v = self.rebuild_tree(v)
            tree[k] = v
        return tree

    @abc.abstractmethod
    def apply(self, tree: ConfigTree, root: object):
        """
        Locally apply the given ConfigTree to the root object.
        :param tree: The ConfigTree to apply.
        :param root: The root object to which the ConfigTree is applied.
        """
        # for attr_name, attr_value in tree.items():
        #     if isinstance(attr_value, ConfigTree):
        #         self.apply(attr_value, eval(f"root.{attr_name}", dict(root=root)))
        #         continue
        #     if attr_name not in dir(root):
        #         warnings.warn(f"{attr_name} not in {root}", RuntimeWarning)
        #     exec(f"root.{attr_name} = attr_value", dict(root=root, attr_value=attr_value))
        pass

    @staticmethod
    def get_config_group(_cls: Any, default=None):
        return getattr(_cls, "__config_group__", default)

    def set_config_group(self, _cls: Any, _config_group=None):
        if _config_group is None:
            _config_group = self
        setattr(_cls, "__config_group__", _config_group)

    @staticmethod
    def is_obj_to_config(_cls: Any, default=False) -> bool:
        return getattr(_cls, "__config__", default)

    def is_obj_of_group(self, _cls: Any, default=None) -> bool:
        """
        Check if the given class is an element of the group.
        :param _cls: The class to check.
        :param default: Default return value if "__config_group__" attribute doesn't exist, usually None or group.
        :return: True if the class is an element of the group, False otherwise.
        """
        return getattr(_cls, "__config_group__", default) == self

    @staticmethod
    def get_config_name(_cls: Any, default=None) -> (str, None):
        return getattr(_cls, "__config_name__", default)

    @staticmethod
    def set_config_name(_cls: Any, _name_value: str):
        setattr(_cls, "__config_name__", _name_value)

    @staticmethod
    def get_config_path(_cls: Any, default=None) -> (str, None):
        return getattr(_cls, "__config_path__", default)

    @staticmethod
    def set_config_path(_cls: Any, _path_value: str):
        setattr(_cls, "__config_path__", _path_value)

    @staticmethod
    def get_included_attr(_cls, default=None) -> Iterable:
        if default is None:
            default = dir(_cls)
        return getattr(_cls, "__config_included__", default)

    @staticmethod
    def set_included_attr(_cls, _value: Iterable):
        setattr(_cls, "__config_included__", _value)

    @staticmethod
    def get_excluded_attr(_cls, default=None) -> Iterable:
        if default is None:
            default = list()
        return getattr(_cls, "__config_excluded__", default)

    @staticmethod
    def set_excluded_attr(_cls, _value: Iterable):
        setattr(_cls, "__config_excluded__", _value)

    @staticmethod
    def is_excluded_attr_name(attr_name: str):
        """
        Check if the attribute should be excluded based on its name,
        you can override this method to exclude some attributes.
        :param attr_name: Name of the attribute to check.
        :return: True if the attribute should be excluded, False otherwise.
        """
        return attr_name.startswith("_")

    def add(self, _obj: Type[_FuncT] = None, check: bool = True, name: str = None, path: str = None) -> _FuncT:
        """
        Add a class to the group.
        """

        def fixer(__obj: Type[_FuncT]) -> _FuncT:
            if not callable(__obj):
                raise TypeError(f"__obj {__obj} is not a callable object")
            if not hasattr(__obj, "__config__"):
                setattr(__obj, "__config__", True)
            if getattr(__obj, "__config__", False) is False:
                return __obj
            if not hasattr(__obj, "__config_group__"):
                __obj.__config_group__ = self
            elif check and __obj.__config_group__ != self:
                warnings.warn(f"the class {__obj} won't be added to {self}, "
                              f"because _cls.__config_group__ = {__obj.__config_group__} != {self}", RuntimeWarning)
                return __obj
            if not self.get_config_name(__obj, False):
                self.set_config_name(__obj, name)
            if not self.get_config_path(__obj, False):
                self.set_config_path(__obj, path)
            self.registered.add(__obj)
            return __obj

        if _obj is None:
            return fixer
        else:
            return fixer(__obj=_obj)

    def __call__(self, cls: Type[_FuncT]) -> _FuncT:
        """
        :param cls: class need to be configured.
        :return: _cls: same class as input.
        """
        return self.add(cls)

    class _Template:
        __config__ = True
        __config_group__: Any
        __config_name__: str
        __config_path__: str
        __config_included__: Iterable
        __config_excluded__: Iterable

    @property
    def Template(self) -> Type[_Template]:
        return self.AbcTemplate
