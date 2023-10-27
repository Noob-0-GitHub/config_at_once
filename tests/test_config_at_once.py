import json

from config_at_once import *

_test_group = Group("test_group")


@_test_group.add
class TestClass:
    default_value = "Default"


def test_group_initialization():
    group = Group("test_group_initialization")
    assert group.name == "test_group_initialization"


def test_add_class_to_group():
    assert TestClass in _test_group.registered


def test_init_config():
    _test_group.init_config(globals())
    assert TestClass.default_value == _test_group.tree["TestClass"]["default_value"]


def test_remove_unserializable_by_objects():
    tree = ConfigTree()
    tree["TestClass"] = ConfigTree({"default_value": "Default", "unserializable_object": object()})
    serializable_tree = tree.remove_unserializable_by_objects(json_serializable_objects)
    assert "unserializable_object" not in serializable_tree["TestClass"]


def test_load_config():
    _test_group.tree["TestClass"]["default_value"] = "Modified"
    json_str = json.dumps(_test_group.tree.remove_unserializable_by_objects(json_serializable_objects))
    _test_group.load_config(json.loads(json_str), globals())
    assert TestClass.default_value == "Modified"
