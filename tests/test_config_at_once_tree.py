import json

import pytest

from config_at_once import *

_test_group = Group("test_group")


@_test_group.add
class TestClass:
    default_value = "Default"

    class TestClassSubIgnore:
        pass


def test_init_config_tree():
    _test_group.init_config(globals(), mode=TREE)
    assert TestClass.default_value == _test_group.tree["TestClass"]["default_value"]


def test_tree_walk():
    @_test_group.add
    class TestClassSub:
        default_value_sub = "DefaultInSub"

        @_test_group.add
        class TestClassSubOfSub:
            default_value_sub_of_sub = "DefaultInSubOfSub"

    TestClass.TestClassSub = TestClassSub

    _test_group.init_config(globals(), mode=TREE)

    assert _test_group.tree["TestClass"]["TestClassSub"]["default_value_sub"] is TestClassSub.default_value_sub
    assert (_test_group.tree["TestClass"]["TestClassSub"]["TestClassSubOfSub"]["default_value_sub_of_sub"] is
            TestClassSub.TestClassSubOfSub.default_value_sub_of_sub)


def test_tree_remove_by_func():
    tree = ConfigTree()
    tree["TestClass"] = ConfigTree({"default_value": "Default",
                                    "unserializable_object": object(),
                                    "ignore_attr": object(),
                                    "None": None
                                    })
    serializable_tree = tree.remove_by_func(check_remove=lambda _o: isinstance(_o, object),
                                            name=True, value=False)
    assert tree["TestClass"]
    assert "unserializable_object" in serializable_tree["TestClass"]
    serializable_tree = tree.remove_by_func(check_remove=lambda name: name.startswith("ignore"),
                                            name=False, value=True)
    assert "ignore_attr" in serializable_tree["TestClass"]
    serializable_tree = tree.remove_by_func(check_remove=lambda name, value: name == str(value),
                                            name=True, value=True)
    assert "None" in serializable_tree["TestClass"]


def test_tree_remove_by_func_raise():
    tree = ConfigTree()
    tree["TestClass"] = ConfigTree({"default_value": "Default"})
    with pytest.raises(ValueError, match="both name and value cannot be False"):
        tree.remove_by_func(check_remove=lambda: True, name=False, value=False)


def test_tree_remove_by_objects():
    tree = ConfigTree()
    tree["TestClass"] = ConfigTree({"default_value": "Default", "unserializable_object": object()})
    serializable_tree = tree.remove_by_objects(json_serializable_objects)
    assert "unserializable_object" not in serializable_tree["TestClass"]


def test_tree_load_config():
    assert _test_group.tree.get("TestClass")
    _test_group.tree["TestClass"]["default_value"] = "Modified"
    json_str = json.dumps(_test_group.tree.remove_by_objects(json_serializable_objects))
    _test_group.load_config(json.loads(json_str), globals(), mode=TREE)
    assert TestClass.default_value == "Modified"
