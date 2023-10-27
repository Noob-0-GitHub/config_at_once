import warnings
from typing import Callable, Iterable, TypeVar, Type

_T = TypeVar('_T')


class ConfigTree(dict):
    def __init__(self, __d=None, group=None):
        super().__init__()
        self.group = group
        if __d is not None:
            self.update(__d)

    def remove_unserializable_by_func(self, check_serializable: Callable, copy: bool = True):
        """
        Remove unserializable objects by check serializable function
        :param check_serializable: function used to check serializable, takes one argument: object
        :param copy: copy or not
        :return: ConfigTree
        """
        if copy:
            tree = self.copy()
        else:
            tree = self

        for k, v in dict.copy(tree).items():
            if isinstance(v, ConfigTree):
                v.remove_unserializable_by_func(check_serializable, copy=False)
            if not check_serializable(v):
                tree.pop(k)
        return tree

    def remove_unserializable_by_objects(self, serializable_objects: Iterable[type] = (object,),
                                         unserializable_objects: Iterable[type] = None, copy: bool = True):
        """
        Remove unserializable objects
        :param serializable_objects: serializable objects
        :param unserializable_objects: objects not serializable
        :param copy: copy or not
        :return: ConfigTree
        """
        if not isinstance(serializable_objects, tuple):
            serializable_objects = tuple(serializable_objects)
        if unserializable_objects is None:
            unserializable_objects = tuple()
        else:
            unserializable_objects = tuple(unserializable_objects)
        if copy:
            tree = self.copy()
        else:
            tree = self

        for k, v in dict.copy(tree).items():
            if isinstance(v, ConfigTree):
                v.remove_unserializable_by_objects(serializable_objects, copy=False)
            elif not isinstance(v, serializable_objects) or isinstance(v, unserializable_objects):
                tree.pop(k)
        return tree

    def copy(self, group=None):
        """
        Copy the tree, but do not copy the elements
        :param group: group of copied ConfigTree
        :return: ConfigTree
        """
        return self.__class__({k: v.copy() if isinstance(v, ConfigTree) else v for k, v in self.items()}, group=group)


class TREE:
    pass


class SCAN:
    pass


class Group:
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.registered: set = set()
        self.tree: ConfigTree = ConfigTree(group=self)

    def init_config(self, root: dict, mode: (TREE, SCAN) = TREE) -> (ConfigTree, None):
        """
        Initialize config
        :param root: root of config, usually be globals() or __dict__
        :param mode: TREE or SCAN
        :return: ConfigTree or None
        """
        self.tree = ConfigTree(group=self)
        if root is None:
            root = globals()
        if mode == TREE:
            for attr_name, value in root.items():
                if getattr(value, "__config__", False) and getattr(attr_name, "__config_group__", self) == self:
                    root[attr_name].__config_path__ = f"{self.name}.{attr_name}"
                    self.tree[attr_name] = self.build_local_tree(value, root[attr_name].__config_path__)
            return self.tree
        elif mode == SCAN:
            pass
        else:
            raise ValueError(f"unknown mode: {mode}")

    def build_local_tree(self, cls: type, check_config: bool = True) -> (ConfigTree, None):
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
        Load config from dict
        :param config_dict: config dict
        :param root: config root, usually be globals() or __dict__
        :param mode: TREE or SCAN
        :return: ConfigTree or None
        """
        if mode == TREE:
            self.tree = self.rebuild_tree(config_dict)
            for attr_name, attr_value in self.tree.items():
                if attr_name not in root:
                    warnings.warn(f"{attr_name} not in {root}", RuntimeWarning)
                    root[attr_name] = attr_value
                if isinstance(attr_value, ConfigTree):
                    self.config_tree_local_apply(attr_value, root[attr_name])
                else:
                    root[attr_name] = attr_value
            # self.config_tree_local_apply(self.tree, root_path)
        elif mode == SCAN:
            pass
        else:
            raise ValueError(f"unknown mode: {mode}")

    def rebuild_tree(self, config_dict: dict) -> ConfigTree:
        tree = ConfigTree(group=self)
        for k, v in config_dict.items():
            if isinstance(v, dict):
                v = self.rebuild_tree(v)
            tree[k] = v
        return tree

    def config_tree_local_apply(self, tree: ConfigTree, root: object):
        for attr_name, attr_value in tree.items():
            if isinstance(attr_value, ConfigTree):
                self.config_tree_local_apply(attr_value, eval(f"root.{attr_name}", dict(root=root)))
                continue
            if attr_name not in dir(root):
                warnings.warn(f"{attr_name} not in {root}", RuntimeWarning)
            exec(f"root.{attr_name} = attr_value", dict(root=root, attr_value=attr_value))

    def is_element_of_group(self, cls: type, default=None):
        return getattr(cls, "__config_group__", default) == self

    @staticmethod
    def attr_exclude(attr_name: str):
        return attr_name.startswith("_")

    def add(self, cls: Type[_T]) -> _T:
        """
        Add a class to the group
        :param cls: class need to be configured
        :return: cls: same class as input
        """
        if not isinstance(cls, type):
            raise TypeError(f"cls must be a class, not {type(cls)}")
        if not hasattr(cls, "__config__"):
            cls.__config__ = True
        if getattr(cls, "__config__", False) is False:
            return cls
        if not hasattr(cls, "__config_group__"):
            cls.__config_group__ = self
        if not hasattr(cls, "__config_path__"):
            cls.__config_path__ = None
        if not hasattr(cls, "__config_include__"):
            cls.__config_only_include__ = dir(cls)
        if not hasattr(cls, "__config_exclude__"):
            cls.__config_exclude__ = list()
        cls.__config_group__ = self
        self.registered.add(cls)
        return cls

    def __call__(self, cls: Type[_T]) -> _T:
        """
        :param cls: class need to be configured
        :return: cls: same class as input
        """
        print(globals().keys())
        return self.add(cls)


json_serializable_objects: list = [bool, int, float, str, dict, list, tuple, type(None)]
