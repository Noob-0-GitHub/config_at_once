
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
