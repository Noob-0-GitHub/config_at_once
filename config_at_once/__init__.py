import warnings
from typing import Callable, Iterable, TypeVar, Type

_T = TypeVar('_T')


class ConfigTree(dict):
    """
    Represents a configuration tree derived from the dictionary class.

    This tree structure aids in managing configuration parameters, providing functionality
    to manipulate, serialize, and deserialize configurations. The class offers methods
    to remove unserializable objects, making it easy to convert the configuration into
    formats such as JSON, INI, XML, or YAML.

    Attributes:
        group: An optional attribute representing the group associated with this ConfigTree.
    """

    def __init__(self, __d=None, group=None):
        """
        Initialize the ConfigTree.
        :param __d: Initial dictionary for the ConfigTree.
        :param group: The group associated with the ConfigTree.
        """
        super().__init__()
        self.group = group
        if __d is not None:
            self.update(__d)

    def remove_by_func(self, check_remove: Callable, name: bool = True, value: bool = True,
                       copy: bool = True):
        """
        Remove objects by check serializable function.
        :param check_remove: a function used to check if the object should be removed, return bool, if return True, remove.
        :param name: args of check_serializable contains attr_name or not. If True, call check_serializable(attr_name).
        :param value: args of check_serializable contains attr_value or not.
        If value is True, call check_serializable(attr_value).
        If name is also True, call check_serializable(attr_name, attr_value).
        When both name and value are False, raise ValueError.
        :param copy: copy or not.
        :return: ConfigTree.
        """
        if copy:
            tree = self.copy()
        else:
            tree = self
        if name is value is False:
            raise ValueError("both name and value cannot be False")

        for k, v in dict.copy(tree).items():
            if isinstance(v, ConfigTree):
                v.remove_by_func(check_remove, name=name, value=value, copy=False)
            if name is value is True:
                if check_remove(k, v):
                    tree.pop(k)
            elif name:
                if check_remove(k):
                    tree.pop(k)
            elif value:
                if check_remove(v):
                    tree.pop(k)
        return tree

    def remove_by_objects(self, allowed_objects: Iterable[type] = (object,),
                          ignored_objects: Iterable[type] = None, copy: bool = True):
        """
        Remove objects.
        :param allowed_objects: serializable objects.
        :param ignored_objects: objects not serializable.
        :param copy: copy or not.
        :return: ConfigTree.
        """
        if not isinstance(allowed_objects, tuple):
            allowed_objects = tuple(allowed_objects)
        if ignored_objects is None:
            ignored_objects = tuple()
        else:
            ignored_objects = tuple(ignored_objects)
        if copy:
            tree = self.copy()
        else:
            tree = self

        for k, v in dict.copy(tree).items():
            if isinstance(v, ConfigTree):
                v.remove_by_objects(allowed_objects, copy=False)
            elif not isinstance(v, allowed_objects) or isinstance(v, ignored_objects):
                tree.pop(k)
        return tree

    def copy(self, group=None):
        """
        Create a copy of the current ConfigTree, but will not copy the elements.
        :param group: Group of copied ConfigTree.
        :return: A new ConfigTree instance.
        """
        return self.__class__({k: v.copy() if isinstance(v, ConfigTree) else v for k, v in self.items()}, group=group)


class TREE:
    """A mode for config"""
    pass


class SCAN:
    """A mode for config"""
    pass


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

    def __init__(self, name):
        """
        Initialize the Group with a name.
        :param name: Name of the group.
        """
        super().__init__()
        self.name = name
        self.registered: set = set()
        self.tree: ConfigTree = ConfigTree(group=self)

    def init_config(self, root: dict, mode: (TREE, SCAN) = TREE) -> (ConfigTree, None):
        """
        Initialize config.
        :param root: root of config, usually be globals() or __dict__.
        :param mode: TREE or SCAN.
        :return: ConfigTree or None.
        """
        self.tree = ConfigTree(group=self)
        if mode == TREE:
            for attr_name, value in root.items():
                if getattr(value, "__config__", False) and getattr(value, "__config_group__", self) == self:
                    root[attr_name].__config_path__ = f"{self.name}.{attr_name}"
                    self.tree[attr_name] = self.build_local_tree(value, root[attr_name].__config_path__)
            return self.tree
        elif mode == SCAN:
            pass
        else:
            raise ValueError(f"unknown mode: {mode}")

    def build_local_tree(self, cls: type, check_config: bool = True) -> (ConfigTree, None):
        """
        Build local tree.
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
                    tree[attr_name] = self.build_local_tree(cls=attr_value, check_config=check_config)
                else:
                    tree[attr_name] = attr_value

        return tree

    def load_config(self, config_dict: dict, root: dict, mode: (TREE, SCAN) = TREE) -> (ConfigTree, None):
        """
        Load config from dict.
        :param config_dict: config dict.
        :param root: config root, usually be globals() or __dict__.
        :param mode: TREE or SCAN.
        :return: ConfigTree or None.
        """
        if mode == TREE:
            self.tree = self.rebuild_tree(config_dict)
            for attr_name, attr_value in self.tree.items():
                if attr_name not in root:
                    warnings.warn(f"{attr_name} no found in {root}", RuntimeWarning)
                    root[attr_name] = attr_value
                if isinstance(attr_value, ConfigTree):
                    self.config_tree_local_apply(attr_value, root[attr_name])
                else:
                    root[attr_name] = attr_value
        elif mode == SCAN:
            pass
        else:
            raise ValueError(f"unknown mode: {mode}")

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

    def add(self, cls: Type[_T]) -> _T:
        """
        Add a class to the group.
        :param cls: class need to be configured.
        :return: cls: same class as input.
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

    def force_add(self, cls: Type[_T]) -> _T:
        """
        Add a class to the group ignoring the "__config__" and "__config_group__".
        :param cls: class need to be forcibly configured.
        :return: cls: same class as input.
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

    def __call__(self, cls: Type[_T]) -> _T:
        """
        :param cls: class need to be configured.
        :return: cls: same class as input.
        """
        return self.add(cls)


json_serializable_objects: list = [bool, int, float, str, dict, list, tuple, type(None)]
