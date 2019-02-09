from abc import ABC, abstractmethod


class GisPoint(ABC):
    _lat = None
    _lon = None

    def __init__(self, lat, lon):
        self._lon = lon
        self._lat = lat
        super().__init__()

    @abstractmethod
    def set_lon(self, lon):
        pass

    @abstractmethod
    def get_lon(self):
        pass

    @abstractmethod
    def set_lat(self, lat):
        pass

    @abstractmethod
    def get_lat(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass
