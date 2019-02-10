from abc import ABC, abstractmethod


class GisPoint(ABC):
    _float_lat = None
    _float_lon = None
    _dms_lat = None
    _dms_lon = None

    def __init__(self, lat, lon):
        super().__init__()

    @abstractmethod
    def set_float_lon(self, lon):
        pass

    @abstractmethod
    def get_float_lon(self):
        pass

    @abstractmethod
    def set_float_lat(self, lat):
        pass

    @abstractmethod
    def get_float_lat(self):
        pass

    @abstractmethod
    def set_dms_lon(self, lon):
        pass

    @abstractmethod
    def get_dms_lon(self):
        pass

    @abstractmethod
    def set_dms_lat(self, lat):
        pass

    @abstractmethod
    def get_dms_lat(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass
