# Unimplemented

from config_at_once import *

_test_group = Group("test_group")


@_test_group.add
class TestClass:
    default_value = "Default"

    class TestClassSub:
        default_value_sub = "Default"


def test_init_config_tree():
    _test_group.init_config(globals(), mode=SCAN)
    pass
