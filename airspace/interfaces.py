from abc import ABC, abstractmethod


class GisPoint(ABC):
    _float_lat = None
    _float_lon = None
    _dms_lat = None
    _dms_lon = None
    crc = None

    def __init__(self, lat, lon, crc):
        super().__init__()
        self.crc = crc

    @abstractmethod
    def set_lon(self, lon):
        pass

    @abstractmethod
    def set_lat(self, lat):
        pass

    @abstractmethod
    def __str__(self):
        pass

    def get_dms_lon(self):
        return self._dms_lon

    def get_dms_lat(self):
        return self._dms_lat

    def get_float_lon(self):
        return self._float_lon

    def get_float_lat(self):
        return self._float_lat

    def __eq__(self, other):
        return (self._float_lat == other.get_float_lat) and (self._dms_lat == other.get_dms_lat) and (
                self._float_lon == other.get_float_lon) and (self._dms_lon == other.get_dms_lon)
