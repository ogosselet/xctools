import logging
import math
import re

import pyproj
from shapely.geometry import Point
from shapely.ops import transform

from airspace.geometry import FloatGisPoint

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


class CircleHelper(object):

    @staticmethod
    def get_circle_points(arc_center_gispoint, arc_radius):
        '''Circle points indexed "lookup" structure

        Args:
            arc_center ([lat, long]): the The geo coord. (lat/long) of the Circle center
            arc_radius ([float]): the radius of the Circle
        '''

        # Cleanup to remove any previous circle "lookup" data from a previous circle
        logger.debug('Cleaning up the arc lookup structure')
        arc_lookup = []
        # Reprojected Circle (v3 because I tried several approach to get a proper circle drawn on a sphere)
        lat = arc_center_gispoint.get_float_lat()
        lon = arc_center_gispoint.get_float_lon()

        AEQD = pyproj.Proj(proj='aeqd', lat_0=lat, lon_0=lon, x_0=lon, y_0=lat)
        WGS84 = pyproj.Proj(init='epsg:4326')

        # transform the given lat-long onto the flat AEQD plane
        tx_lon, tx_lat = pyproj.transform(WGS84, AEQD, lon, lat)
        circle = Point(tx_lat, tx_lon).buffer(arc_radius)

        def inverse_tx(x, y, z=None):
            x, y = pyproj.transform(AEQD, WGS84, x, y)
            return (x, y)

        # inverse projection from AEQD to EPSG4326-WGS84
        points = transform(inverse_tx, circle)

        for i, point in enumerate(points):
            fpoint = FloatGisPoint(point[1], point[0], i, "circle_point")
            arc_lookup.append(fpoint)
        return arc_lookup


class GisPointFactory(object):

    @staticmethod
    def build_border_point(lat, lon, code_type, crc):
        lat = GisUtil.format_decimal_degree(lat)
        lon = GisUtil.format_decimal_degree(lon)
        return FloatGisPoint(lat, lon, crc, code_type)

    @staticmethod
    def build_circle_point_list(circle_element):
        # Collect the center & the radius of the Circle
        center_lat = circle_element.find('geoLatCen').text
        center_lon = circle_element.find('geoLongCen').text
        center_crc = circle_element.find('valCrc').text
        arc_center = FloatGisPoint(center_lat, center_lon, center_crc, "arc_center")

        # Collect the radius
        arc_radius = GisUtil.format_geo_size(circle_element.find('valRadius').text,
                                             circle_element.find('uomRadius').text)
        return CircleHelper.get_circle_points(arc_center, arc_radius)

    @staticmethod
    def build_free_geometry_point_list(xml_point_list):
        for xml_point in xml_point_list:
            code_type= xml_point.find('codeType').text
            if code_type == 'GRC':
                pass
            elif code_type=='RHL':
                pass
            elif code_type=='FNT':
                pass
            elif code_type=='CCA':
                pass
            elif code_type=='CWA':
                pass
            elif code_type=='':
                pass
