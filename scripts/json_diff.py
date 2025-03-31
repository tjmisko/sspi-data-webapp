import json
import sys


def json_diff(json1, json2) -> (list, list):
    """
    Compare two JSON objects (lists of objects) and return the symmetric differences.
    Args:
        json1 list[dict]: The first JSON object.
        json2 list[dict]: The second JSON object.
    Returns:
        list: A list containing two lists - the first list contains keys only in json1,
              and the second list contains keys only in json2.
    """
    def equiv(a, b) -> bool:
        if isinstance(a, str) and isinstance(b, str):
            return a == b
        return abs(a - b) < 1e-5

    def check(obs1: dict, obs2: dict) -> bool:
        for key, value in obs1.items():
            if not (key in obs2 and equiv(obs2[key], value)):
                return False
        return True

    only_in_json1 = []
    only_in_json2 = []
    for obj1 in json1:
        found = False
        for obj2 in json2:
            if check(obj1, obj2):
                found = True
                break
        if not found:
            only_in_json1.append(obj1)
    for obj2 in json2:
        found = False
        for obj1 in json1:
            if check(obj2, obj1):
                found = True
                break
        if not found:
            only_in_json2.append(obj2)
    return only_in_json1, only_in_json2


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python json_diff.py <json1_file> <json2_file>")
        sys.exit(1)
    json1_file = sys.argv[1]
    json2_file = sys.argv[2]
    with open(json1_file, 'r') as f:
        json1 = json.load(f)
    with open(json2_file, 'r') as f:
        json2 = json.load(f)
    only_in_1, only_in_2 = json_diff(json1, json2)
    print(json.dumps({"only_in_1": only_in_1, "only_in_2": only_in_2}, indent=4))
