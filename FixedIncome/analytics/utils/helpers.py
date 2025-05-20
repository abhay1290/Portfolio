import math


def replace_nan_with_none(d):
    for k, v in d.items():
        if isinstance(v, float) and math.isnan(v):
            d[k] = None
        elif isinstance(v, dict):
            replace_nan_with_none(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    replace_nan_with_none(item)
    return d
