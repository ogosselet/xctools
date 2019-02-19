from __future__ import absolute_import, division, print_function

import logging
import math
import re

import pyproj
from lxml import etree
from shapely.geometry import Point
from shapely.ops import transform

from airspace.interfaces import GisPoint

logger = logging.getLogger(__name__)

geod = pyproj.Geod(ellps='WGS84')

FREE_GEOM = 1
CIRCLE_GEOM = 2


class AixmSource(object):
    """Class to process Airspace information contained in an AIXM 4.5 source file

    This class should implement all the method expected by the Airspace class to
    collect all the relevant information present in the source (admin info, geo info, ...)
    and normalize the return data to our XCTools format
    """

    __filename = None
    __tree = None
    __borders = None
    __air_spaces = None
    __root = None

    def __init__(self, filename):
        """Initialize the AIXM source

        Args:
            filename ([type]): the file system file containing the AIXM 4.5 Airspace Informations
        """

        self.__filename = filename
        self.__tree = etree.parse(self.__filename)
        self.__root = self.__tree.getroot()
        self.__borders = []
        self.__air_spaces = []
        self.parse_xml()

    def parse_xml(self):
        self.parse_borders()
        self.parse_air_spaces()

    def parse_air_spaces(self):
        for admin_data in self.__root.findall('Ase'):
            air_space = Airspace()
            uid = admin_data.find('AseUid')
            air_space.uuid = uid.get('mid')
            air_space.code_type = uid.find('codeType').text
            air_space.code_id = uid.find('codeId').text
            air_space.text_name = admin_data.find('txtName').text
            air_space.code_Activity = admin_data.find('codeActivity').text
            air_space.code_dist_ver_upper = admin_data.find('codeDistVerUpper').text
            air_space.val_dist_ver_upper = admin_data.find('valDistVerUpper').text
            air_space.uom_dist_ver_upper = admin_data.find('uomDistVerUpper').text
            air_space.code_dist_ver_lower = admin_data.find('codeDistVerLower').text
            air_space.val_dist_ver_lower = admin_data.find('valDistVerLower').text
            air_space.uom_dist_ver_lower = admin_data.find('uomDistVerLower').text
            air_space.codeWorkHr = admin_data.find('Att').find('codeWorkHr').text
            air_space.remark = admin_data.find('txtRmk').text
            self.add_air_space(air_space)

        for space in self.__root.findall('Abd'):
            uuid = space.find('AbdUid').get('mid')
            air_space = self.get_air_space(uuid)
            circle_xml_element = space.findall('Circle')
            if len(circle_xml_element) > 0:
                air_space.polygon_points = GisPointFactory.build_circle_point_list(circle_xml_element)
            else:
                xml_points = space.findall('Avx')
                air_space.polygon_points, air_space.border_crossings = GisPointFactory.build_free_geometry_point_list(
                    xml_points, self)

    def parse_borders(self):
        for border in self.__root.findall('Gbr'):
            border_object = Border
            uid = border.find('GbrUid')
            border_object.uuid = uid.get('mid')
            border_object.text_name = uid.find('txtName')
            border_object.code_type = border.find('codeType').text
            for point in border.findall('Gbv'):
                print(etree.tostring(point))
                lat = point.find('geoLat')
                lon = point.find('geoLon')
                c_type = point.find('codeType')
                crc = point.find('valCrc')
                print(etree.tostring(lon))
                point_object = GisPointFactory.build_border_point(lat.text,
                                                                  lon.text,
                                                                  c_type.text,
                                                                  crc.text)
                border_object.append_border_point(point_object)
            self.add_border(border_object)

    def list_air_spaces(self):
        str_out = ""
        for air_space in self.__air_spaces:
            str_out += air_space.text_name + '\n'

        return str_out

    def get_air_spaces(self):
        return self.__air_spaces

    def get_borders(self):
        return self.__borders

    def get_air_space(self, mid_uuid):
        return next(x for x in self.__air_spaces if x.uuid == mid_uuid)

    def get_border(self, mid_uuid):
        return next(x for x in self.__borders if x.uuid == mid_uuid)

    def add_border(self, border_object):
        self.__borders.append(border_object)

    def add_air_space(self, air_space_object):
        self.__air_spaces.append(air_space_object)


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

    @staticmethod
    def extract_arc_points(direction, arc_center, arc_radius, arc_start, arc_stop):
        '''Extract a subset of Circle points forming a specific Arc of Circle

        TODO: confirm the arc_radius needs to be in meter

        Args:
            direction ([-1, 1]): Counter clockwise (-1) or clockwise (1) direction to move on circle
            arc_center ([lat, long]): The geo coord. (lat/long) of the Arc center
            arc_radius ([float]): The radius of the Arc
            arc_start ([lat, long]): The geo coord. (lat/long) of the start point of the Arc
            arc_stop ([lat, long]): The geo coord. (lat/long) of the end point of the Arc

        Returns:
            [list]: a list of coordinates that can be used to create a "Polygon"
        '''

        logger.debug('Extracting Arc')

        circle_points = []

        lat = arc_center.get_float_lat()
        lon = arc_center.get_float_lon()

        AEQD = pyproj.Proj(proj='aeqd', lat_0=lat, lon_0=lon, x_0=lon, y_0=lat)
        WGS84 = pyproj.Proj(init='epsg:4326')

        # transform the given lat-long onto the flat AEQD plane
        tx_lon, tx_lat = pyproj.transform(WGS84, AEQD, lon, lat)
        circle = Point(tx_lat, tx_lon).buffer(arc_radius)

        def inverse_tx(x, y, z=None):
            x, y = pyproj.transform(AEQD, WGS84, x, y)
            return (x, y)

        # inverse projection from AEQD to EPSG4326-WGS84
        projected_circle = transform(inverse_tx, circle)

        projected_circle_points = projected_circle.exterior.coords

        for i, point in enumerate(projected_circle_points):
            gis_point = FloatGisPoint(point[1], point[0], i, "circle_point")
            circle_points.append(gis_point)

        # Finding the closest surrounding points around the start/stop points of our Arc on the Circle
        # idx_ are tupples of point index on the circle
        idx_start = CircleHelper.get_idx_around_arc_point(arc_start.get_float_lat(), arc_start.get_float_lon(),
                                                          circle_points)
        idx_stop = CircleHelper.get_idx_around_arc_point(arc_stop.get_float_lat(), arc_stop.get_float_lon(),
                                                         circle_points)

        # The actual extraction of the points
        return CircleHelper.get_arc_points(direction, idx_start, idx_stop, circle_points)

    @staticmethod
    def get_idx_around_arc_point(latitude, longitude, circle_points):
        '''Define the index of the 2 circle points that are the closest from a POI (lat, long).

        The POI is on or very close from the circle.
        We measure the distance between 2 point and our POI as follow using Pythagore

          - sqr(distance) = sqr(delta_lat) + sqr(delta_long)

        We compute a cumulated distance by summing up the 2 sqr(distance)

        The 2 consecutive circle points minimizing this cumulated distance are the interesting
        point of the circle.

        The main difference with the "Border" equivalent method is that we use in this case
        an integer value that we add on each and every circle point as "index" lookup value
        for the extraction

        Args:
            latitude ([float]): Geo Lat. in decimal degree of the POI we want to locate on the circle
            longitude ([float]): Geo Long. in decimal degree of the POI we want to locate on the circle

        Returns:
            [tupple]: the 2 index of the circle points surrounding our POI
        '''

        logger.debug('Finding position on Arc for Lat:%s / Long:%s', latitude, longitude)
        # TODO: replace with "max float" or a meaningfull max distance ever possible on earth
        min_distance = float(1000000000000)
        idx_left = ''
        idx_right = ''
        # TODO: converge more quickly if once prooven to be slow to process
        for i in range(len(circle_points) - 1):
            geo_lat_1 = circle_points[i].get_float_lat()
            geo_long_1 = circle_points[i][1].get_float_lon()
            geo_lat_2 = circle_points[i + 1].get_float_lat()
            geo_long_2 = circle_points[i + 1].get_float_lon()

            # Compute the distance
            distance = (latitude - geo_lat_1) ** 2 + \
                       (longitude - geo_long_1) ** 2 + \
                       (geo_lat_2 - latitude) ** 2 + \
                       (geo_long_2 - longitude) ** 2

            # Looking up the minimum
            if distance < min_distance:
                min_distance = distance
                idx_left = circle_points[i].crc  # crc is the idx in pyproj generated points
                idx_right = circle_points[i + 1].crc  # crc is the idx in pyproj generated points

        return idx_left, idx_right

    @staticmethod
    def get_arc_points(direction, idx_start, idx_stop, circle_points):

        '''Get the subset of the Arc point in the good direction

        Args:
            direction (-1, 1): counter-clockwise=-1, clockwise=1
            index_start ([tupple]): the index of the 2 points around our first border point
            index_stop ([type]): the index of the 2 points around our last border point
        '''

        # Remember that index_ are still tupple for now.
        # Let's first define the direction in which need to navigate the border

        if direction == 1 and (idx_start[0] < idx_stop[0]):
            # We can just extract the points
            start = max(idx_start)
            stop = min(idx_stop) + 1
            return circle_points[start:stop]

        if direction == 1 and (idx_start[0] > idx_stop[0]):
            # We need to pass over 0

            # There is 2 extraction
            #     from max(idx_start) to the end
            start = max(idx_start)
            start_list = circle_points[start:]
            #     from 0 to min(idx_stop) + 1
            stop = min(idx_stop) + 1
            end_list = circle_points[0:stop]
            logger.debug('Extracting in CW direction from %s to %s', start, stop)
            return start_list + end_list

        # Counter Clockwise
        if direction == -1 and (idx_start[0] < idx_stop[0]):
            # We can just extract the points
            start = min(idx_start) + 1
            stop = max(idx_stop)
            return list(reversed(circle_points[0:start])) + list(reversed(circle_points[stop:]))

        if direction == -1 and (idx_start[0] > idx_stop[0]):
            # We need to pass over 0

            # There is 2 extraction
            #     from max(idx_start) to the end
            start = max(idx_stop)
            stop = min(idx_start) + 1
            return list(reversed(circle_points[start:stop]))


class BorderHelper(object):

    @staticmethod
    def extract_border_points(border_object, previous_point, current_point):
        crc_start = BorderHelper._get_crc_around_border_point(previous_point, border_object)
        crc_stop = BorderHelper._get_crc_around_border_point(current_point, border_object)

        index_start = BorderHelper.get_border_indexes(border_object, crc_start)
        index_stop = BorderHelper.get_border_indexes(border_object, crc_stop)

        # Remember that index_ are still tupple for now.
        # Let's first define the direction in which need to navigate the border
        if index_start[0] < index_stop[0]:
            forward = True
            start = max(index_start)
            stop = min(index_stop) + 1
        else:
            forward = False
            start = min(index_start) + 1
            stop = max(index_stop)

        if forward:
            return border_object.border_points[start:stop]
        else:
            return list(reversed(border_object.border_points[stop:start]))

    @staticmethod
    def get_border_indexes(border_object, crc_start):
        index_start = []
        for index, border_point in enumerate(border_object.border_points):
            if border_point[2] == crc_start[0]:
                index_left = index
                break
        for index, border_point in enumerate(border_object.border_points):
            if border_point[2] == crc_start[1]:
                index_right = index
                break
        index_start.append(index_left)
        index_start.append(index_right)
        return index_start

    @staticmethod
    def _get_crc_around_border_point(gis_point_object, border_object):
        min_distance = float(1000000000000)
        crc_left = ''
        crc_right = ''
        for i in range(len(border_object.border_points) - 1):
            geo_lat_1 = border_object.border_points[i].get_float_lat()
            geo_long_1 = border_object.border_points[i].get_float_lon()
            geo_lat_2 = border_object.border_points[i + 1].get_float_lat()
            geo_long_2 = border_object.border_points[i + 1].get_float_lon()

            distance = (gis_point_object.get_float_lat() - geo_lat_1) ** 2 + \
                       (gis_point_object.get_float_lon() - geo_long_1) ** 2 + \
                       (geo_lat_2 - gis_point_object.get_float_lat()) ** 2 + \
                       (geo_long_2 - gis_point_object.get_float_lon()) ** 2

            if distance < min_distance:
                min_distance = distance
                crc_left = border_object.border_points[i].crc
                crc_right = border_object.border_points[i + 1].crc

        return crc_left, crc_right


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
    def build_free_geometry_point_list(xml_point_list, aixm_source):
        current_point = None
        gis_data = []
        border_crossings = []
        for xml_point in xml_point_list:
            previous_point = current_point
            code_type = xml_point.find('codeType').text
            current_point = FloatGisPoint(xml_point.find('geoLat').text, xml_point.find('geoLong').text,
                                          xml_point.find('valCrc').text, code_type)
            if previous_point is not None:
                if code_type == 'GRC' or code_type == 'RHL':
                    gis_data.append(previous_point)
                elif code_type == 'FNT':
                    border_uuid = xml_point.find('GbrUid').get('mid')
                    gis_data.append(previous_point)
                    border_obj = aixm_source.get_border(border_uuid)
                    border_points = BorderHelper.extract_border_points(border_obj, previous_point, current_point)
                    gis_data.extend(border_points)
                    crossing = BorderCrossing(border_uuid, border_obj.text_name)
                    crossing.common_points.extend(border_points)
                    border_crossings.append(crossing)
                elif code_type == 'CCA':
                    # Collect the center & the radius of the Circle Arc

                    arc_center = FloatGisPoint(xml_point.find('geoLatArc').text, xml_point.find('geoLongArc').text,
                                               xml_point.find('valCrc').text + "center", "CCA_CENTER")

                    arc_radius = GisUtil.format_geo_size(
                        value=xml_point.find('valRadiusArc').text,
                        unit=xml_point.find('uomRadiusArc').text
                    )
                    # We pile up the first point
                    gis_data.append(previous_point)

                    # Counter Clockwise = -1
                    gis_data.extend(
                        CircleHelper.extract_arc_points(-1, arc_center, arc_radius, previous_point, current_point))

                elif code_type == 'CWA':
                    # Collect the center & the radius of the Circle Arc

                    arc_center = FloatGisPoint(xml_point.find('geoLatArc').text, xml_point.find('geoLongArc').text,
                                               xml_point.find('valCrc').text + "center", "CCA_CENTER")

                    arc_radius = GisUtil.format_geo_size(
                        value=xml_point.find('valRadiusArc').text,
                        unit=xml_point.find('uomRadiusArc').text
                    )
                    # We pile up the first point
                    gis_data.append(previous_point)

                    # Counter Clockwise = -1
                    gis_data.extend(
                        CircleHelper.extract_arc_points(1, arc_center, arc_radius, previous_point, current_point))

        return gis_data, border_crossings


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
