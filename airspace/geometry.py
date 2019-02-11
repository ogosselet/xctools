from __future__ import absolute_import, division, print_function

import logging
import math
import re

import pyproj
from shapely.geometry import Point

from .exceptions import AirspaceGeomUnknown
from .interfaces import GisPoint

logger = logging.getLogger(__name__)

geod = pyproj.Geod(ellps='WGS84')

FREE_GEOM = 1
CIRCLE_GEOM = 2


class GisUtil:

    @staticmethod
    def truncate(f, n):
        """Truncates/pads a float f to n decimal places without rounding"""
        s = '{}'.format(f)
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        return float('.'.join([i, (d + '0' * n)[:n]]))

    @staticmethod
    def format_vertical_limit(code, value, unit):

        # TODO: AGL/AMSL ? Ft/FL ? ...
        return '{}-{}-{}'.format(code, value, unit)

    @staticmethod
    def format_geo_size(value, unit):

        # TODO: cover all possible unit
        if unit == "NM":
            return float(value) * 1852
        if unit == "KM":
            return float(value) * 1000

    @staticmethod
    def compute_distance(geo_pt1, geo_pt2):
        """Compute great circle distance between 2 points

        TODO: Not really used but we might reuse it to compute the "mean" circle radius

        Args:
            geo_center ([latitude, longitude]): the geo coordinates of the first point
            geo_point ([latitude, longitude]): the geo coordinates of the second point
        """

        dstproj = pyproj.Proj('+proj=ortho +lon_0=%f +lat_0=%f' % (geo_pt1[0], geo_pt2[1]))
        srcproj = pyproj.Proj(ellps='WGS84', proj='latlong')
        new_cx, new_cy = pyproj.transform(srcproj, dstproj, geo_pt1[0], geo_pt1[1])
        new_px, new_py = pyproj.transform(srcproj, dstproj, geo_pt2[0], geo_pt2[1])
        radius = Point(new_cx, new_cy).distance(Point(new_px, new_py))
        logger.debug('Computed radius by shapely %s', radius)
        azimuth1, azimuth2, radius2 = geod.inv(geo_pt1[0], geo_pt1[1], geo_pt2[0], geo_pt2[1])
        logger.debug('Computed radius by pyproj only %s', radius2)

    @staticmethod
    def dms2dd(degree, minute, second, decimal=0):
        """Degree Minute Second (Decimal) => Decimal Degree

        Args:
            degree ([int]): number or string repr. of integer
            minute ([int]): number or string repr. of integer
            second ([int]): number or string repr. of integer
            decimal ([float]): optional decimal of seconds in the form 0.xxxxx

        Returns:
            [float]: the Decimal Degree
        """

        return float(degree) + float(minute) / 60 + float(second) / 3600 + float(decimal) / 3600

    @staticmethod
    def dd2dms(dd, is_longitude):
        """Decimal Degree => Degree Minute Second (Decimal)

        Args:
            dd ([float]):  floating point decimal repr.
            is_longitude([boolean]):  boolean that indicate whether dd is longitude or latitude.
        Returns:
            [string]: string representation of the decimal coordinate
        """
        split_deg = math.modf(dd)
        degrees = int(split_deg[1])
        minutes = abs(int(math.modf(split_deg[0] * 60)[1]))
        seconds = abs(round(math.modf(split_deg[0] * 60)[0] * 60, 2))

        minutes_fmt = '{0:02d}'.format(minutes)

        sec_decim, sec_int = math.modf(seconds)

        seconds_fmt = '{0:02d}'.format(int(sec_int))
        seconds_fmt += '.'
        seconds_fmt += '{0:.2f}'.format(sec_decim).split('.')[1]
        if is_longitude:
            degrees_fmt = '{0:03d}'.format(degrees)
            if degrees < 0:
                suffix = "W"
            else:
                suffix = "E"
        else:
            degrees_fmt = '{0:02d}'.format(degrees)
            if degrees < 0:
                suffix = "S"
            else:
                suffix = "N"

        return degrees_fmt + minutes_fmt + seconds_fmt + suffix

    @staticmethod
    def format_decimal_degree(coordinate_string):
        """Detect a coordinate format & perform the transformation to Decimal Degree

        Works for string representation of Latitude or Longitude

        North Latitude & East Longitude return a positive value
        South Latitude & West Longitude return a negative value

        Args:
            coordinate_string ([str]): the input coordinate string that we will auto-detect

        Returns:
            [float]: a decimal degree coordinate value
        """

        # Expected format:
        # - Decimal degree (51.089056N or 002.545428E)
        #       Convert to float, define the sign N=(+), S=(-), W=(+), E=(-)

        # - Degree Minute Second w/wo Decimal (510521.37N, 494137N or 0051624E, ...
        #       Convert to Decimal Degree, Convert to float, define the sign N=(+), S=(-), W=(+), E=(-)

        # Latitude Decimal Degree => Floating & Signing
        lat_string = re.match(r'(\d{2})\.(\d{1,6})([N,S])', coordinate_string)
        if lat_string:
            if lat_string.group(3) == 'N':
                sign = 1
            else:
                sign = -1
            return sign * float(coordinate_string[:-1])

        # Longitude Decimal Degree => Floating & Signing
        long_string = re.match(r'(\d{3})\.(\d{1,6})([W,E])', coordinate_string)
        if long_string:
            if long_string.group(3) == 'W':
                sign = -1
            else:
                sign = 1
            return sign * float(coordinate_string[:-1])

        # Latitude Degree Minute Second (& Opt. Decimal Second) => dms2dd conversion
        lat_string = re.match(r'(\d{2})(\d{2})(\d{2})(\.\d{1,6})?([N,S])', coordinate_string)
        if lat_string:
            if lat_string.group(5) == 'N':
                sign = 1
            else:
                sign = -1

            if lat_string.group(4):
                decimal = lat_string.group(4)
            else:
                decimal = '0'

            return sign * GisUtil.dms2dd(
                degree=lat_string.group(1),
                minute=lat_string.group(2),
                second=lat_string.group(3),
                decimal=decimal
            )

        # Longitude Degree Minute Second (& Opt. Decimal Second) => dms2dd conversion
        long_string = re.match(r'(\d{3})(\d{2})(\d{2})(\.\d{1,6})?([W,E])', coordinate_string)
        if long_string:
            if long_string.group(5) == 'W':
                sign = -1
            else:
                sign = 1

            if long_string.group(4):
                decimal = long_string.group(4)
            else:
                decimal = '0'

            return sign * GisUtil.dms2dd(
                degree=long_string.group(1),
                minute=long_string.group(2),
                second=long_string.group(3),
                decimal=decimal
            )
        # TODO: Raise an exception if we received a format not supported


class FloatGisPoint(GisPoint):
    __accuracy = None

    def __init__(self, lat, lon, crc, accuracy=5):
        self.__accuracy = accuracy
        super().__init__(lat, lon, crc)

    def set_lon(self, lon):
        self._float_lon = GisUtil.truncate(lon, self.__accuracy)
        self._dms_lon = GisUtil.dd2dms(lon, True)

    def set_lat(self, lat):
        self._float_lat = GisUtil.truncate(lat, self.__accuracy)
        self._dms_lat = GisUtil.dd2dms(lat, False)

    def __str__(self):
        return '[' + str(self._float_lon) + ', ' + str(self._float_lat) + ']'


class DmsGisPoint(GisPoint):

    def __init__(self, lat, lon, crc):
        super().__init__(lat, lon, crc)

    def set_lon(self, lon):
        self._float_lon = GisUtil.format_decimal_degree(lon)
        self._dms_lon = GisUtil.dd2dms(self._float_lon, True)

    def set_lat(self, lat):
        self._float_lat = GisUtil.format_decimal_degree(lat)
        self._dms_lat = GisUtil.dd2dms(self._float_lat, False)

    def __str__(self):
        return '[' + str(self._dms_lon) + ', ' + str(self._dms_lat) + ']'


class GisDataFactory(object):

    @staticmethod
    def parse_element(self, xml_element, ase_uid):
        gis_data = []
        if xml_element[0].xpath('Circle'):
            # do stuffs with circles not sure what is returned in that case
            logger.debug('Circle geometry detected')
        elif xml_element[0].xpath('Avx'):
            # do stuff with Avx
            logger.debug('Free geometry detected')
            for avx_elem in xml_element[0].xpath('Avx'):
                # Willingly over simplified for code clarity (this is a proof of concept before optional rewrite)
                if avx_elem.xpath('codeType/text()')[0] == 'GRC':
                    gis_point = GisPoint(GisUtil.format_decimal_degree(avx_elem.xpath('geoLat/text()')[0]),
                                         GisUtil.format_decimal_degree(avx_elem.xpath('geoLong/text()')[0]),
                                         avx_elem.xpath('valCrc/text()')[0])
                    gis_data.append(gis_point)
        else:
            raise AirspaceGeomUnknown(self, ase_uid)
        return gis_data


class Airspace(object):
    __uuid = None
    polygon_points = None
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

    def __init__(self):
        super.__init__()


class Border(object):
    __border_points = None
    __uuid = None
    __code_type = None
    __text_name = None

    def __init__(self):
        super.__init__()
