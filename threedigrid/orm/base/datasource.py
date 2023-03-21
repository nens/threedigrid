# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.


class DataSource:
    """
    Datasource containing a 'dict' like object
    acting as the main datasource for the gridadmin
    models.
    """

    meta = None
    _source = None

    def __init__(self, source, meta=None, gridadmin=None):
        self.meta = meta
        self._source = source
        self._gridadmin = gridadmin

    def keys(self):
        keys = list(self._source.keys())
        # Append meta to keys if not present
        if "meta" not in keys:
            keys.append("meta")
        return keys

    def set(self, name, value):
        raise NotImplementedError()

    def get(self, name):
        # meta is special
        if name == "meta":
            return self.meta
        return self._source.get(name)

    def __getitem__(self, name):
        # meta is special
        if name == "meta":
            return self.meta
        return self._source[name]
