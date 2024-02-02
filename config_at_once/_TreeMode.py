import os.path

from .config_tree import ConfigTree
from .utils import *


class Group:
    """
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

    def __init__(self, path: str, name: str):
        """
        Initialize ConfigGroup.
        :param path: The saving path of the config group.
        :param name: Name of the group.
        """
        super().__init__()
        self.path = path
        self.name = name
        self.registered: set = set()
        self.tree: ConfigTree = ConfigTree(group=self)
        # for attr_name, value in root.items():
        #     if getattr(value, "__config__", False) and getattr(value, "__config_group__", self) == self:
        #         root[attr_name].__config_path__ = f"{self.name}.{attr_name}"
        #         self.tree[attr_name] = self._build_local_tree(value, root[attr_name].__config_path__)

    def _build_local_tree(self, cls: type, check_config: bool = True) -> (ConfigTree, None):
        """
        Build LocalTree.
        :param cls:
        :param check_config:
        :return: ConfigTree or None.
        """
        if check_config:
            if not getattr(cls, "__config__", False) or not self.is_element_of_group(cls):
                return None
        if getattr(cls, "__config_path__", None) is None:
            cls.__config_path__ = f"{self.name}.{cls.__name__}"
        cls_path: str = str(getattr(cls, "__config_path__"))
        tree = ConfigTree(group=self)
        for attr_name in getattr(cls, "__config_include__", dir(cls)):
            if attr_name not in getattr(cls, "__config_exclude__", []) and not self.attr_exclude(attr_name):
                attr_value = getattr(cls, attr_name)
                if getattr(cls, "__config__", False) and self.is_element_of_group(attr_value):
                    attr_value.__config_path__ = f"{cls_path}.{attr_name}"
                    tree[attr_name] = self._build_local_tree(cls=attr_value, check_config=check_config)
                else:
                    tree[attr_name] = attr_value

        return tree

    def load(self):
        if os.path.exists(self.path):
            pass
        else:
            pass

    def save_to_dict(self):
        pass

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
                self.config_tree_local_apply(attr_value, root[attr_name])
            else:
                root[attr_name] = attr_value

    def save_to_file(self, path: str = None):
        if path is None:
            path = self.path
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

    def load_from_file(self, path: str):
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

    def load_from_ini(self, path: str):
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(path)
            self.load_from_dict(config, globals())
        except ImportError:
            raise ImportError("The module configparser is not installed")

    def load_from_json(self, path: str):
        try:
            import json
            with open(path, "r") as f:
                self.load_from_dict(json.load(f), globals())
        except ImportError:
            raise ImportError("The module json is not installed")

    def load_from_yaml(self, path: str):
        try:
            import yaml
            with open(path, "r") as f:
                self.load_from_dict(yaml.load(f, Loader=yaml.FullLoader), globals())
        except ImportError:
            raise ImportError("The module yaml is not installed")

    def load_from_toml(self, path: str):
        try:
            import toml
            with open(path, "r") as f:
                self.load_from_dict(toml.load(f), globals())
        except ImportError:
            raise ImportError("The module toml is not installed")

    def load_from_xml(self, path: str):
        try:
            import xmltodict
            with open(path, "r") as f:
                self.load_from_dict(xmltodict.parse(f), globals())
        except ImportError:
            raise ImportError("The module xmltodict is not installed")

    def reload(self):
        pass

    def resave(self):
        pass

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

    def config_tree_local_apply(self, tree: ConfigTree, root: object):
        """
        Locally apply the given ConfigTree to the root object.
        :param tree: The ConfigTree to apply.
        :param root: The root object to which the ConfigTree is applied.
        """
        for attr_name, attr_value in tree.items():
            if isinstance(attr_value, ConfigTree):
                self.config_tree_local_apply(attr_value, eval(f"root.{attr_name}", dict(root=root)))
                continue
            if attr_name not in dir(root):
                warnings.warn(f"{attr_name} not in {root}", RuntimeWarning)
            exec(f"root.{attr_name} = attr_value", dict(root=root, attr_value=attr_value))

    def is_element_of_group(self, cls: type, default=None):
        """
        Check if the given class is an element of the group.
        :param cls: The class to check.
        :param default: Default return value if "__config_group__" attribute doesn't exist, usually None or group.
        :return: True if the class is an element of the group, False otherwise.
        """
        return getattr(cls, "__config_group__", default) == self

    @staticmethod
    def attr_exclude(attr_name: str):
        """
        Check if the attribute should be excluded based on its name,
        you can override this method to exclude some attributes.
        :param attr_name: Name of the attribute to check.
        :return: True if the attribute should be excluded, False otherwise.
        """
        return attr_name.startswith("_")

    def add(self, cls: Type[T]) -> T:
        """
        Add a class to the group.
        :param cls: Class need to be configured.
        :return: cls: Same class as input.
        """
        if not isinstance(cls, type):
            raise TypeError(f"cls must be a class, not {type(cls)}")
        if not hasattr(cls, "__config__"):
            cls.__config__ = True
        if getattr(cls, "__config__", False) is False:
            return cls
        if not hasattr(cls, "__config_group__"):
            cls.__config_group__ = self
        elif cls.__config_group__ != self:
            warnings.warn(f"the class {cls} won't be added to {self}, "
                          f"because cls.__config_group__ = {cls.__config_group__} != {self}", RuntimeWarning)
            return cls
        if not hasattr(cls, "__config_path__"):
            cls.__config_path__ = None
        if not hasattr(cls, "__config_include__"):
            cls.__config_only_include__ = dir(cls)
        if not hasattr(cls, "__config_exclude__"):
            cls.__config_exclude__ = list()
        self.registered.add(cls)
        return cls

    def force_add(self, cls: Type[T]) -> T:
        """
        Add a class to the group ignoring the "__config__" and "__config_group__".
        :param cls: Class need to be forcibly configured.
        :return: cls: Same class as input.
        """
        if not isinstance(cls, type):
            raise TypeError(f"cls must be a class, not {type(cls)}")
        cls.__config__ = True
        cls.__config_group__ = self
        if not hasattr(cls, "__config_path__"):
            cls.__config_path__ = None
        if not hasattr(cls, "__config_include__"):
            cls.__config_only_include__ = dir(cls)
        if not hasattr(cls, "__config_exclude__"):
            cls.__config_exclude__ = list()
        self.registered.add(cls)
        return cls

    def __call__(self, cls: Type[T]) -> T:
        """
        :param cls: class need to be configured.
        :return: cls: same class as input.
        """
        return self.add(cls)
