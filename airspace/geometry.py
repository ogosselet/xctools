import re
import logging
import pyproj

from .exceptions import AirspaceGeomUnknown
from __future__ import absolute_import, division, print_function
from shapely.geometry import Point

logger = logging.getLogger(__name__)

geod = pyproj.Geod(ellps='WGS84')

FREE_GEOM = 1
CIRCLE_GEOM = 2


class GisUtil:

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


class GisPoint(object):
    __lat = None
    __long = None
    __crc = None
    __precision = 5

    def __init__(self, lat, lon, crc):
        self.set_lon(lon)
        self.set_lat(lat)
        self.set_crc(crc)

    def truncate(self, f, n):
        """Truncates/pads a float f to n decimal places without rounding"""
        s = '{}'.format(f)
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        return '.'.join([i, (d + '0' * n)[:n]])

    def set_lon(self, lon):
        self.lon = float(self.truncate(lon, self.__precision))

    def get_lon(self):
        return self.lon

    def set_lat(self, lat):
        self.__lat = float(self.truncate(lat, self.__precision))

    def get_lat(self):
        return self.__lat

    def set_crc(self, crc):
        self.__crc = crc

    def get_crc(self):
        return self.__crc

    def __str__(self):
        return '[' + str(self.lon) + ', ' + str(self.__lat) + ', ' + str(self.__crc) + ']'

    # Now you can compare if 2 GisPoint are equals (== or assertEqual() )
    # if we implement __lt__, __le__, __gt__ and __ge__ GisPoint could be sortable (don't know if it is use full)
    def __eq__(self, other):
        return (self.get_lon() == other.get_lon()) and (self.get_lat() == other.get_lat()) and (
                    self.get_crc() == other.get_crc())


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
