from itertools import chain


def _flatten_dict_values(d, as_set=False):
    """
    :param d: input dictionary
    :param as_set: return the flattened values as set
        (removes duplicates), default is False
    :return: list of dictionary values, if as_set as been set to True
        the set of values

    :raises TypeError if the dict values are deeper nested than [[x]]
    """

    return_func = set if as_set else list
    _values = d.values()
    if any(isinstance(i, list) for i in _values):
        return return_func(chain(*_values))
    else:
        return return_func(_values)
