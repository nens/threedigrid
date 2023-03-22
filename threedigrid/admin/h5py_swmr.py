import h5py


class H5SwmrFile(h5py.File):
    """
    Override h5py file access, to
    automatically refresh datasets and make
    sure we only have one reference to one dataset
    """

    def __init__(self, path, file_modus):
        self._datasets = {}
        super().__init__(path, file_modus, swmr=True)

        # By default register all datasets
        for key in self.keys():
            self.get(key)

    def get(self, key):
        return self.__getitem__(key)

    def refresh_datasets(self):
        for _, dataset in self._datasets.items():
            dataset.refresh()

    def __getitem__(self, key):
        """
        Store datasets pointers in owned dictionairy
        """
        if key in self._datasets:
            return self._datasets[key]

        res = super().__getitem__(key)
        if isinstance(res, h5py.Dataset):
            if key not in self._datasets:
                self._datasets[key] = res
        return res
