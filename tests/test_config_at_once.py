import pytest

from config_at_once import *


def test_group_initialization():
    group = Group("test_group_initialization")
    assert group.name == "test_group_initialization"


def test_add_class_to_group():
    local_test_group = Group("local_test_group")

    @local_test_group.add
    class LocalTestClass:
        pass

    assert LocalTestClass in local_test_group.registered


def test_add_class_to_group_by_call():
    local_test_group = Group("local_test_group")

    @local_test_group
    class LocalTestClass:
        pass

    assert LocalTestClass in local_test_group.registered


def test_init_config_unknown_mode():
    local_test_group = Group("local_test_group")

    with pytest.raises(ValueError, match="unknown mode: unknown_mode"):
        local_test_group.init_config(globals(), mode="unknown_mode")


def test_init_config_ignore():
    local_test_group = Group("local_test_group")

    @local_test_group.add
    class TestClassIgnore:
        __config__ = False

    assert TestClassIgnore not in local_test_group.registered


def test_init_config_group_ignore():
    local_test_group = Group("local_test_group")
    another_group = Group("another_group")

    @local_test_group.add
    class TestClassGroupIgnore:
        __config_group__ = another_group

    assert TestClassGroupIgnore not in local_test_group.registered


def test_force_add_ignoring_config():
    local_test_group = Group("local_test_group")

    @local_test_group.force_add
    class TestClass:
        __config__ = False

    assert TestClass in local_test_group.registered


def test_force_add_ignoring_config_group():
    local_test_group = Group("local_test_group")
    another_group = Group("another_group")

    @local_test_group.force_add
    class TestClass:
        __config_group__ = another_group

    assert TestClass in local_test_group.registered
