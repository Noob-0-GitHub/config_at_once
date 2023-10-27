import json

from config_at_once import *

group_test = Group("test")


@group_test.add
class Test:
    @group_test
    class TestSub:
        default_value1_of_sub = "TestSub"

    default_value1 = "Test"
    unserializable_object = object()


group_test.init_config(globals())
print(json.dumps(group_test.tree.remove_unserializable_by_objects(json_serializable_objects), indent=2))
group_test.tree["Test"]["default_value1"] = "Test_load"
json_str = json.dumps(group_test.tree.remove_unserializable_by_objects(json_serializable_objects), indent=2)

print(json_str)
group_test.load_config(json.loads(json_str), globals())
print(Test.default_value1)
