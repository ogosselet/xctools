"""
Author : Ludovic Reenaers (https://github.com/Djang0)
Inspired by the work of Olivier Gosselet (https://github.com/ogosselet/xctools)


This module contains abstract classes to describe interface
"""
from abc import ABC, abstractmethod


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
    crc = None
    code_type = None

    def __init__(self, crc, code_type):
        """
        :param str crc: unique reference of GisPoint
        :param str code_type: type of GisPoint
        """
        super().__init__()
        self.crc = crc
        self.code_type = code_type

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
    def __str__(self):
        """
        :return : string representation of the GisPoint
        :rtype: str
        """
        pass

    def get_oa_lon(self):
        """
        get OpenAir formatted longitude
        :rtype: str
        """
        coord, letter = self._dms_lon.split('.')
        return coord[0:3] + ":" + coord[3:5] + ":" + coord[5:7] + letter[-1]

    def get_oa_lat(self):
        """
        get OpenAir formatted latitude
        :rtype: str
        """
        coord, letter = self._dms_lat.split('.')
        return coord[0:2] + ":" + coord[2:4] + ":" + coord[4:6] + letter[-1]

    def get_dms_lon(self):
        """
        get dms formatted longitude
        :rtype: str
        """
        return self._dms_lon

    def get_dms_lat(self):
        """
        get dms formatted latitude
        :rtype: str
        """
        return self._dms_lat

    def get_float_lon(self):
        """
        get float value of longitude
        :rtype: float
        """
        return self._float_lon

    def get_float_lat(self):
        """
        get float value latitude
        :rtype: float
        """
        return self._float_lat

    def __eq__(self, other):
        """
        test if this is equals to other
        :param other: GisPoint that is compared to this
        :tyype other : airspace.interfaces.GisPoint
        :return: True if equals
        :rtype: bool
        """
        return (self._float_lat == other.get_float_lat) and (self._dms_lat == other.get_dms_lat) and (
                self._float_lon == other.get_float_lon) and (self._dms_lon == other.get_dms_lon)
