from __future__ import absolute_import, division, print_function

from airspace.interfaces import GisPoint
from airspace.util import GisUtil


class FloatGisPoint(GisPoint):
    __accuracy = None

    def __init__(self, lat, lon, crc, code_type, accuracy=5):
        super().__init__(crc, code_type)
        self.__accuracy = accuracy
        self.set_lat(lat)
        self.set_lon(lon)

    def set_lon(self, lon):
        self._float_lon = GisUtil.truncate(lon, self.__accuracy)
        self._dms_lon = GisUtil.dd2dms(lon, True)

    def set_lat(self, lat):
        self._float_lat = GisUtil.truncate(lat, self.__accuracy)
        self._dms_lat = GisUtil.dd2dms(lat, False)

    def __str__(self):
        return '[' + str(self._float_lon) + ', ' + str(self._float_lat) + ']'


class DmsGisPoint(GisPoint):

    def __init__(self, lat, lon, crc, code_type):
        super().__init__(crc, code_type)
        self.set_lat(lat)
        self.set_lon(lon)

    def set_lon(self, lon):
        self._float_lon = GisUtil.format_decimal_degree(lon)
        self._dms_lon = GisUtil.dd2dms(self._float_lon, True)

    def set_lat(self, lat):
        self._float_lat = GisUtil.format_decimal_degree(lat)
        self._dms_lat = GisUtil.dd2dms(self._float_lat, False)

    def __str__(self):
        return '[' + str(self._dms_lon) + ', ' + str(self._dms_lat) + ']'


class Airspace(object):
    uuid = None
    polygon_points = []
    code_type = None
    code_id = None
    text_name = None
    code_Activity = None
    code_dist_ver_upper = None
    val_dist_ver_upper = None
    uom_dist_ver_upper = None
    code_dist_ver_lower = None
    val_dist_ver_lower = None
    uom_dist_ver_lower = None
    codeWorkHr = None
    remark = None
    border_crossings = []

    def __init__(self):
        super.__init__()

    def get_border_intersections(self, border_uuid):
        return (x for x in self.border_crossings if x.uuid == border_uuid)


class BorderCrossing(object):
    related_border_uuid = None
    related_border_name = None
    common_points = []

    def __init__(self, related_border_uuid, related_border_name):
        super().__init__()
        self.related_border_name = related_border_name
        self.related_border_uuid = related_border_uuid


class Border(object):
    uuid = None
    code_type = None
    text_name = None
    border_points = []

    def __init__(self):
        super.__init__()

    def append_border_point(self, gis_point_object):
        self.border_points.append(gis_point_object)

    def get_border_point(self, crc):
        return next(x for x in self.border_points if x.crc == crc)
