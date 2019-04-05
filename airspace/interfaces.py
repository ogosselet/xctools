"""
Author : Ludovic Reenaers (https://github.com/Djang0)
Inspired by the work of Olivier Gosselet (https://github.com/ogosselet/xctools)


This module contains abstract classes to describe interface
"""
from abc import ABC, abstractmethod


class Sourceable(ABC):
    _borders = None
    _air_spaces = None

    def __init__(self, airspaces=[], borders=[]):

        self._parse_borders(borders)
        self._parse_air_spaces(airspaces)

    @abstractmethod
    def _parse_air_spaces(self, borders) -> None:
        pass

    @abstractmethod
    def _parse_borders(self, airspaces) -> None:
        pass

    @abstractmethod
    def get_air_spaces(self) -> list:
        pass

    @abstractmethod
    def get_borders(self) -> list:
        pass

    @abstractmethod
    def get_air_space(self, mid_uuid: str):
        pass

    @abstractmethod
    def get_border(self, mid_uuid: str):
        pass

    @abstractmethod
    def add_border(self, border_object) -> None:
        pass

    @abstractmethod
    def add_air_space(self, air_space_object) -> None:
        pass

    def to_dict(self) -> dict:
        as_list = []
        for ais in self._air_spaces:
            as_list.append(ais.to_dict())

        border_list = []
        for bor in self._borders:
            border_list.append(bor.to_dict())

        source_dict = {
            "air_spaces": as_list,
            "borders": border_list
        }
        return source_dict


class GisPoint(ABC):
    """
    Interface describing GisPoint, used to draw vectors or polygons

    Attributes:
        _float_lat  float value representing latitude
        _float_lon  float value representing longitude
        _dms_lat    str value representing dms latitude
        _dms_lon    str value representing dms longitude
        crc         str representing unique point identifier
        code_type   str representing type of GisPoint

    """
    _float_lat = None
    _float_lon = None
    _dms_lat = None
    _dms_lon = None
    _accuracy = None

    crc = None
    code_type = None

    def __init__(self, crc: str, code_type: str, accuracy: str):
        """
        :param str crc: unique reference of GisPoint
        :param str code_type: type of GisPoint
        """
        super().__init__()
        self.crc = crc
        self.code_type = code_type
        self._accuracy = accuracy

    @abstractmethod
    def set_lon(self, lon):
        """
        defines longitude for the class implementing the interfaces
        :param lon: type defined by implementation
        """
        pass

    @abstractmethod
    def set_lat(self, lat):
        """
        defines latitude for the class implementing the interfaces
        :param lat: type defined by implementation
        """
        pass

    @abstractmethod
    def __str__(self) -> str:
        """
        :return : string representation of the GisPoint
        :rtype: str
        """
        pass

    def get_oa_lon(self) -> str:
        """
        get OpenAir formatted longitude
        :rtype: str
        """
        coord, letter = self._dms_lon.split('.')
        return coord[0:3] + ":" + coord[3:5] + ":" + coord[5:7] + letter[-1]

    def get_oa_lat(self) -> str:
        """
        get OpenAir formatted latitude
        :rtype: str
        """
        coord, letter = self._dms_lat.split('.')
        return coord[0:2] + ":" + coord[2:4] + ":" + coord[4:6] + letter[-1]

    def get_dms_lon(self) -> str:
        """
        get dms formatted longitude
        :rtype: str
        """
        return self._dms_lon

    def get_dms_lat(self) -> str:
        """
        get dms formatted latitude
        :rtype: str
        """
        return self._dms_lat

    def get_float_lon(self) -> float:
        """
        get float value of longitude
        :rtype: float
        """
        return self._float_lon

    def get_float_lat(self) -> float:
        """
        get float value latitude
        :rtype: float
        """
        return self._float_lat

    def get_accuracy(self) -> int:
        return self._accuracy

    def to_dict(self) -> dict:
        point_dict = {
            "float_lat": self.get_float_lat(),
            "float_lon": self.get_float_lon(),
            "dms_lat": self.get_dms_lat(),
            "dms_lon": self.get_dms_lon(),
            "openair_lat": self.get_oa_lat(),
            "openair_lon": self.get_oa_lon(),
            "decimal _accuracy": self.get_accuracy(),
            "crc": self.crc,
            "code_type": self.code_type,
        }
        return point_dict

    def __eq__(self, other) -> bool:
        """
        test if this is equals to other
        :param other: GisPoint that is compared to this
        :tyype other : airspace.interfaces.GisPoint
        :return: True if equals
        :rtype: bool
        """
        a = (self.get_float_lat() == other.get_float_lat())
        b = (self.get_dms_lat() == other.get_dms_lat())
        c = (self.get_float_lon() == other.get_float_lon())
        d = (self.get_dms_lon() == other.get_dms_lon())
        eq = a and b and c and d
        return eq
