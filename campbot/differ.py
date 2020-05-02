import difflib


def get_diff_report(old, new):
    old = flatten(old)
    new = flatten(new)

    keys = set(list(old.keys()) + list(new.keys()))
    result = []

    for key in sorted(keys):
        if key not in old:
            result.append("+++ {} : {}".format(key, repr(new[key])))

        elif key not in new:
            result.append("--- {} : {}".format(key, repr(old[key])))

        elif old[key] != new[key]:
            if isinstance(old[key], (int, bool, float)) or (
                len(old[key]) < 20 and len(new[key]) < 20
            ):
                result.append(("^^^ {} : {} >>> {}".format(key, old[key], new[key])))
            else:
                d = difflib.Differ()
                diff = d.compare(
                    old[key].replace("\r", "").split("\n"),
                    new[key].replace("\r", "").split("\n"),
                )

                report = "\n    ".join(
                    dd.replace("\n", "") for dd in diff if dd[0] != " "
                )
                result.append("^^^ {} :\n    {}".format(key, report))

    return result


def flatten(source, root_path="root"):
    try:
        base_types = (unicode, str, int, long, float, bool)  # py 2.7
    except NameError:
        base_types = (str, int, float, bool)  # py 3

    result = {}

    def worker(obj, path):
        if obj is None:
            pass

        elif isinstance(obj, base_types):
            result[path] = obj

        elif isinstance(obj, dict):
            for key, item in obj.items():
                worker(item, path + "." + key)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                worker(item, path + "[" + str(i) + "]")

        else:
            raise Exception("{} type is not supported".format(type(obj)))

    worker(source, root_path)

    return result
