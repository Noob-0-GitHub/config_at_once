from ._abc import AbcGroup
from .config_tree import ConfigTree
from .utils import *

_FuncT = TypeVar("_FuncT")


class Group(AbcGroup):
    def _build_config_tree(self, root: dict):
        tree = ConfigTree(group=self)
        treed_obj = set()
        for attr_name, value in root.items():
            if self.is_obj_to_config(value) and self.is_obj_of_group(value):
                tree[attr_name] = self._build_local_config_tree(attr_name, value, treed_obj=treed_obj)
        for untreed_obj in self.registered.difference(treed_obj):
            if self.get_config_path(untreed_obj) is not None:
                # tree.path_index(self.get_config_path(untreed_obj)) = self._build_local_config_tree(
                #     self.get_config_name(untreed_obj), untreed_obj)
                pass
            else:
                pass

    def _build_local_config_tree(self, cls_name: str, _cls: Any, check_if_to_config: bool = True,
                                 treed_obj: (list, set) = None) -> (ConfigTree, None):
        """
        Build LocalTree.
        :param check_if_to_config:
        :return: ConfigTree or None.
        """
        if check_if_to_config:
            if not self.is_obj_to_config(_cls) or not self.is_obj_of_group(_cls):
                return None
        if self.get_config_name(_cls) is not None:
            cls_name = self.get_config_name(_cls)
        if self.get_config_path(_cls) is None:
            cls_path: str = ConfigTree.config_path_join(self.name, cls_name)
            self.set_config_path(_cls, cls_path)
        else:
            cls_path: str = self.get_config_path(_cls)
            if not isinstance(cls_path, str):
                if self.WARNING:
                    pass
                cls_path: str = ConfigTree.config_path_join(self.name, cls_name)
                self.set_config_path(_cls, cls_path)
        tree = ConfigTree(group=self)
        if treed_obj is not None:
            if isinstance(treed_obj, list):
                treed_obj.append(_cls)
            elif isinstance(treed_obj, set):
                treed_obj.add(_cls)
        # for attr_name in getattr(_cls, "__config_include__", dir(_cls)):
        for attr_name in self.get_included_attr(_cls):
            # if attr_name in getattr(_cls, "__config_exclude__", []) or self.is_excluded_attr_name(attr_name):
            if attr_name in self.get_excluded_attr(_cls) or self.is_excluded_attr_name(attr_name):
                continue
            attr_value = getattr(_cls, attr_name, None)
            if self.is_obj_to_config(_cls) and self.is_obj_of_group(attr_value):
                self.set_config_path(attr_value, ConfigTree.config_path_join(cls_path, attr_name))  # NB
                tree[attr_name] = self._build_local_config_tree(attr_name, attr_value, check_if_to_config, treed_obj)
            else:
                tree[attr_name] = attr_value
        return tree

    def save_to_dict(self) -> None:
        pass

    def load_from_dict(self, config_dict: dict, root: dict) -> (ConfigTree, None):
        pass

    def apply(self, tree: ConfigTree, root: object):
        pass
