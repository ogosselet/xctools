"""
Author : Ludovic Reenaers (https://github.com/Djang0)
Inspired by the work of Olivier Gosselet (https://github.com/ogosselet/xctools)


This module classes for Aixml source file parsing
"""
from __future__ import absolute_import, division, print_function

import logging
import math
import re
import os

import pyproj
import simplekml
from lxml import etree
from shapely.geometry import Point
from shapely.ops import transform

from airspace.interfaces import GisPoint, Sourceable

logger = logging.getLogger(__name__)

geod = pyproj.Geod(ellps='WGS84')

FREE_GEOM = 1
CIRCLE_GEOM = 2


class BorderCrossing(object):
    """
    Class representing the intersection of a border in an airspace

    Attributes:

        related_border_uuid     The uuid of the related border
        related_border_name     The display name of the related border
        common_points           A list of airspace.interfaces.GisPoint crossing the border
    """
    related_border_uuid = None
    related_border_name = None
    common_points = []

    def __init__(self, related_border_uuid, related_border_name):
        """
        Constructor method
        :param str related_border_uuid: The uuid of the related border
        :param str related_border_name: The display name of the related border
        """
        super().__init__()
        self.related_border_name = related_border_name
        self.related_border_uuid = related_border_uuid

    def to_dict(self) -> dict:
        point_list = []
        for point in self.common_points:
            point_list.append(point.to_dict())
        crossing_dict = {
            "related_border_uuid": self.related_border_uuid,
            "related_border_name": self.related_border_name,
            "common_points": point_list
        }
        return crossing_dict


class Border(object):
    """
    Class representing Aixm border item

    Attributes:
        uuid            Unique reference of the border from within the source file.
                            for generated points, this should be unique as well
        code_type       The type of point, as described within source file. might be generated as well
        text_name       display name of the border as mentioned in source file
        border_points   list of airspace.interfaces.GisPoint representing the border.
    """
    uuid = None
    code_type = None
    text_name = None
    border_points = []

    def __init__(self):
        super().__init__()
        self.border_points = []

    def append_border_point(self, gis_point_object) -> None:
        """
        Adds a GisPoint to the border vector

        :param airspace.interfaces.GisPoint gis_point_object: border point
        """
        self.border_points.append(gis_point_object)

    def get_border_point(self, crc) -> GisPoint:
        """
        Returns a GisPoint belonging to border vector, using its crc

        :param str crc: GisPoint's crc
        :return: GisPoint
        :rtype: airspace.interfaces.GisPoint
        """
        point = None
        try:
            point = next(x for x in self.border_points if x.crc == crc)
        except:
            pass
        return point

    def to_dict(self) -> dict:
        point_list = []
        for point in self.border_points:
            point_list.append(point.to_dict())
        border_dict = {
            "uuid": self.uuid,
            "code_type": self.code_type,
            "text_name": self.text_name,
            "border_coords": point_list
        }
        return border_dict


class Airspace(object):
    """
    A class representation of an airspace.

    Attributes:
        uuid                The unique identifier of the airspace
        polygon_points      A list of airspace.interfaces.GisPoint representing airspace geometry
        code_type           The type of airspace
        code_id             The numerical code identifier of the airspace
        text_name           The display name of the airspace
        code_Activity       The activity code of the airspace
        code_dist_ver_upper The upper vertical distance  code
        val_dist_ver_upper  The value of the upper vertical distance
        uom_dist_ver_upper  The uom of the upper vertical distance
        code_dist_ver_lower The lower vertical distance code
        val_dist_ver_lower  The value of the lower vertical distance
        uom_dist_ver_lower  The uom of the upper vertical distance
        codeWorkHr          Code for the working hours (when airspace is activated)
        remark              Remarks
        border_crossings    A list of airspace.source.BorderCrossing instances
    """
    uuid = None
    polygon_points = []
    code_type = None
    code_id = None
    text_name = None
    code_activity = None
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
        super().__init__()

    def get_border_intersection(self, border_uuid) -> BorderCrossing:
        """
        Returns an airspace.sources.BorderCrossing object that matches border_uuid. Otherwise, returns None.

        :param str border_uuid: The uuid of the related border
        :return: The requested airspace.sources.BorderCrossing object
        :rtype: airspace.sources.BorderCrossing or None
        """
        crossing = None
        try:
            crossing = next(x for x in self.border_crossings if x.uuid == border_uuid)
        except:
            pass
        return crossing

    def to_kml(self, target_directory: str) -> None:
        # TODO : implement some color factory in order to avoid having the same color for every airspace
        kml = simplekml.Kml()
        pol = kml.newpolygon(name=self.text_name)
        pol.style.linestyle.color = simplekml.Color.red
        pol.style.linestyle.width = 1
        pol.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.red)
        outerboundaryis = []
        for point in self.polygon_points:
            outerboundaryis.append((point.get_float_lon(), point.get_float_lat()))
        # Close the polygon
        outerboundaryis.append((self.polygon_points[0].get_float_lon(), self.polygon_points[0].get_float_lat()))
        pol.outerboundaryis = outerboundaryis
        outputfile = os.path.join(target_directory, '{}.kml'.format(self.text_name))
        kml.save(outputfile)

    def to_dict(self) -> dict:
        crossing_list = []
        for crossing in self.border_crossings:
            crossing_list.append(crossing.to_dict())
        point_list = []
        for point in self.polygon_points:
            point_list.append(point.to_dict())

        json_dict = {
            "uuid": self.uuid,
            "code_type": self.code_type,
            "code_id": self.code_id,
            "text_name": self.text_name,
            "code_Activity": self.code_activity,
            "code_dist_ver_upper": self.code_dist_ver_upper,
            "val_dist_ver_upper": self.val_dist_ver_upper,
            "uom_dist_ver_upper": self.uom_dist_ver_upper,
            "code_dist_ver_lower": self.code_dist_ver_lower,
            "val_dist_ver_lower": self.val_dist_ver_lower,
            "uom_dist_ver_lower": self.uom_dist_ver_lower,
            "codeWorkHr": self.codeWorkHr,
            "remark": self.remark,
            "polygon": point_list,
            "border_crossings": crossing_list
        }
        return json_dict


class AixmSource(Sourceable):
    """Class to process Airspace information contained in an AIXM 4.5 source file

    This class should implement all the method expected by the Airspace class to
    collect all the relevant information present in the source (admin info, geo info, ...)
    and normalize the return data to our XCTools format
    """

    __filename = None
    __tree = None
    __root = None

    def __init__(self, filename, airspaces=[], borders=[]):
        """Initialize the AIXM source

        Args:
            filename ([type]): the file system file containing the AIXM 4.5 Airspace Informations
        """

        self.__filename = filename
        self.__tree = etree.parse(self.__filename)
        self.__root = self.__tree.getroot()
        self._borders = []
        self._air_spaces = []
        super().__init__(airspaces, borders)

    def _parse_air_spaces(self, airspaces) -> None:
        for admin_data in self.__root.findall('Ase'):
            air_space = Airspace()
            uid = admin_data.find('AseUid')
            air_space.uuid = uid.get('mid')
            air_space.code_type = uid.find('codeType').text
            air_space.code_id = uid.find('codeId').text
            try:
                air_space.text_name = admin_data.find('txtName').text
            except Exception as exc:
                air_space.text_name = ''

            # Looks like codeActivity is not in all Airspace
            try:
                air_space.code_activity = admin_data.find('codeActivity').text
            except Exception as exc:
                air_space.code_activity = ''
            try:
                air_space.code_dist_ver_upper = admin_data.find('codeDistVerUpper').text
            except Exception as exc:
                air_space.code_dist_ver_upper = ''
            try:
                air_space.val_dist_ver_upper = admin_data.find('valDistVerUpper').text
            except Exception as exc:
                air_space.val_dist_ver_upper = '0'
            try:
                air_space.uom_dist_ver_upper = admin_data.find('uomDistVerUpper').text
            except Exception as exc:
                air_space.uom_dist_ver_upper = ''
            try:
                air_space.code_dist_ver_lower = admin_data.find('codeDistVerLower').text
            except Exception as exc:
                air_space.code_dist_ver_lower = '0'
            try:
                air_space.val_dist_ver_lower = admin_data.find('valDistVerLower').text
            except Exception as exc:
                air_space.val_dist_ver_lower = ''
            try:
                air_space.uom_dist_ver_lower = admin_data.find('uomDistVerLower').text
            except Exception as exc:
                air_space.uom_dist_ver_lower = ''
            try:
                air_space.codeWorkHr = admin_data.find('Att').find('codeWorkHr').text
            except Exception as exc:
                air_space.codeWorkHr = ''
            try:
                air_space.remark = admin_data.find('txtRmk').text
            except Exception as exc:
                air_space.remark = ''
            self.add_air_space(air_space)

        if len(airspaces) != 0:
            # We are not in list mode, we are actually parsing airspaces
            for space in self.__root.findall('Abd'):
                uuid = space.find('AbdUid').get('mid')
                if uuid in airspaces:
                    # We can process the full parsing
                    air_space = self.get_air_space(uuid)
                    circle_xml_element = space.find('Circle')
                    if circle_xml_element is not None:
                        air_space.polygon_points = GisPointFactory.build_circle_point_list(circle_xml_element)
                    else:
                        xml_points = space.findall('Avx')
                        try:
                            air_space.polygon_points, air_space.border_crossings = GisPointFactory.build_free_geometry_point_list(
                                xml_points, self)
                        except Exception as exc:
                            logger.debug(air_space)
                else:
                    # We skip the expensive parsing for the other airspaces
                    pass

    def _parse_borders(self, borders) -> None:

        for border in self.__root.findall('Gbr'):
            border_object = Border()
            uid = border.find('GbrUid')
            border_object.uuid = uid.get('mid')
            border_object.text_name = uid.find('txtName').text
            border_object.code_type = border.find('codeType').text

            # We are not in list mode, we are actually parsing airpsaces
            if len(borders) != 0:

                for point in border.findall('Gbv'):
                    lat = point.find('geoLat')
                    lon = point.find('geoLong')
                    c_type = point.find('codeType')
                    crc = point.find('valCrc')

                    point_object = GisPointFactory.build_float_point(lat.text,
                                                                 lon.text,
                                                                 c_type.text,
                                                                 crc.text)
                    border_object.append_border_point(point_object)
            self.add_border(border_object)

    def get_air_spaces(self) -> list:
        return self._air_spaces

    def get_borders(self) -> list:
        return self._borders

    def get_air_space(self, mid_uuid: str) -> Airspace:
        """

        Args:
            mid_uuid:

        Returns:

        """
        air_space = None
        try:
            air_space = next(x for x in self._air_spaces if x.uuid == mid_uuid)
        except StopIteration:
            pass
        return air_space

    def get_border(self, mid_uuid: str) -> Border:
        border = None
        try:
            border = next(x for x in self._borders if x.uuid == mid_uuid)
        except StopIteration:
            pass
        return border

    def add_border(self, border_object: Border) -> None:
        self._borders.append(border_object)

    def add_air_space(self, air_space_object: Airspace) -> None:
        self._air_spaces.append(air_space_object)


class GisUtil:
    """
    Util class that provides static method for Gis handling
    """

    @staticmethod
    def truncate(f: float, n: int) -> float:
        """
        Truncates/pads a float f to n decimal places without rounding

        :param float f: The number to be truncated / padded
        :param int n: the amount of decimal to use for truncation / padding
        :return: the padded / truncated float
        :rtype: float
        """
        s = '{}'.format(f)
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        return float('.'.join([i, (d + '0' * n)[:n]]))

    @staticmethod
    def format_vertical_limit(code: str, value: str, unit: str) -> str:

        # TODO: AGL/AMSL ? Ft/FL ? ...
        return '{}-{}-{}'.format(code, value, unit)

    @staticmethod
    def format_geo_size(value: str, unit: str) -> str:

        # TODO: cover all possible unit
        if unit == "NM":
            return float(value) * 1852
        if unit == "KM":
            return float(value) * 1000
        if unit == "M":
            return float(value)
        if unit == "FT":
            return float(value) * 0.3048

    @staticmethod
    def compute_distance(geo_center: GisPoint, geo_point: GisPoint) -> None:
        """Compute great circle distance between 2 points

        TODO: Not really used but we might reuse it to compute the "mean" circle radius

        Args:
            geo_center ([latitude, longitude]): the geo coordinates of the first point
            geo_point ([latitude, longitude]): the geo coordinates of the second point
        """

        dstproj = pyproj.Proj(
            '+proj=ortho +lon_0=%f +lat_0=%f' % (geo_center.get_gloat_lon(), geo_point.get_float_lat()))
        srcproj = pyproj.Proj(ellps='WGS84', proj='latlong')
        new_cx, new_cy = pyproj.transform(srcproj, dstproj, geo_center.get_float_lat(), geo_center.get_float_lon())
        new_px, new_py = pyproj.transform(srcproj, dstproj, geo_point.get_float_lat(), geo_point.get_float_lon())
        radius = Point(new_cx, new_cy).distance(Point(new_px, new_py))
        logger.debug('Computed radius by shapely %s', radius)
        azimuth1, azimuth2, radius2 = geod.inv(geo_center.get_float_lat(), geo_center.get_float_lon(),
                                               geo_point.get_float_lat(), geo_point.get_float_lon())
        logger.debug('Computed radius by pyproj only %s', radius2)

    @staticmethod
    def dms2dd(degree: int, minute: int, second: int, decimal: float = 0) -> float:
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
    def dd2dms(dd: float, is_longitude: bool) -> str:
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
    def format_decimal_degree(coordinate_string: str) -> float:
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
    """
    Helper class that provides static method for circle drawing
    """

    @staticmethod
    def get_circle_points(arc_center_gispoint: GisPoint, arc_radius: float) -> list:
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
        projected_circle_points = points.exterior.coords
        for i, point in enumerate(projected_circle_points):
            fpoint = FloatGisPoint(point[1], point[0], i, "circle_point")
            arc_lookup.append(fpoint)
        return arc_lookup

    @staticmethod
    def extract_arc_points(direction: int, arc_center: GisPoint, arc_radius: float, arc_start: GisPoint,
                           arc_stop: GisPoint) -> list:
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
    def get_idx_around_arc_point(latitude: float, longitude: float, circle_points: list) -> tuple:
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
            geo_long_1 = circle_points[i].get_float_lon()
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
    def get_arc_points(direction: int, idx_start: tuple, idx_stop: tuple, circle_points: list) -> list:

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
    """
    Helper class providing static methods in order to handle border drawing.
    """

    @staticmethod
    def extract_border_points(border_object: Border, previous_point: GisPoint, current_point: GisPoint) -> list:
        """
        Extract border points between two points.

        :param airspace.sources.Border border_object:
        :param airspace.interfaces.GisPoint previous_point:
        :param airspace.interfaces.GisPoint current_point:
        :return: a list of airspace.interfaces.GisPoint implementation
        :rtype: list
        """
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
    def get_border_indexes(border_object: Border, crc_start: tuple) -> list:
        """
        Returns border point indexes from a given point's crc

        :param airspace.sources.Border border_object: The border to search in
        :param str crc_start: the crc of the point
        :return: a list containing index start and index stop
        :rtype: list
        """
        index_start = []
        for index, border_point in enumerate(border_object.border_points):
            if border_point.crc == crc_start[0]:
                index_left = index
                break
        for index, border_point in enumerate(border_object.border_points):
            if border_point.crc == crc_start[1]:
                index_right = index
                break
        index_start.append(index_left)
        index_start.append(index_right)
        return index_start

    @staticmethod
    def _get_crc_around_border_point(gis_point_object: GisPoint, border_object: Border) -> tuple:
        """
        Returns the nearest left and right crc of a point within a given border
        :param airspace.interfaces.GisPoint gis_point_object:
        :param airspace.sources.Border border_object:
        :return: both crc
        :rtype: tuple
        """
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
    """
    A Factory for building airspace.interfaces.GisPoint
    """

    @staticmethod
    def build_float_point(lat: str, lon: str, code_type: str, crc: str) -> GisPoint:
        """
        Build a point object from data string

        :param str lat: latitude in DMS as from Aixm Source file
        :param str lon: latitude in DMS as from Aixm Source file
        :param str code_type: type of point
        :param str crc: The unique code of a point
        :return: An implementation of airspace.interfaces.GisPoint
        :rtype: airspace.sources.FloatGisPoint
        """
        lat = GisUtil.format_decimal_degree(lat)
        lon = GisUtil.format_decimal_degree(lon)
        return FloatGisPoint(lat, lon, crc, code_type)

    @staticmethod
    def build_circle_point_list(circle_element: etree._Element) -> list:
        """
        Build a list of airspace.interfaces.GisPoint implementation from the given lxml circle element

        :param lxml.etree.Element circle_element: xml representation of circle element from Aixm source file
        :return: a list of airspace.interfaces.GisPoint implementation
        :rtype: list
        """
        # Collect the center & the radius of the Circle
        center_lat = GisUtil.format_decimal_degree(circle_element.find('geoLatCen').text)
        center_lon = GisUtil.format_decimal_degree(circle_element.find('geoLongCen').text)
        center_crc = circle_element.find('valCrc').text
        arc_center = FloatGisPoint(center_lat, center_lon, center_crc, "arc_center")

        # Collect the radius
        arc_radius = GisUtil.format_geo_size(circle_element.find('valRadius').text,
                                             circle_element.find('uomRadius').text)
        return CircleHelper.get_circle_points(arc_center, arc_radius)

    def build_free_geometry_point_list(xml_point_list: list, aixm_source: AixmSource) -> tuple:
        """
        Build free geometry airspace polygon.

        :param lxml.etree.Element xml_point_list: a list of xml element representing airspace points geometry
        :param airspace.sources.AixmSource aixm_source: An instance of airspace.sources.AixmSource
        :return: a list of airspace.interfaces.GisPoint implementation
        :rtype: list
        """
        current_point = None
        gis_data = []
        border_crossings = []
        point_buffer = ['', '']
        codetype_buffer = ['', '']


        for xml_point in xml_point_list:


            # In an AVX, there is always a reference to a point
            # We will store this point in a sliding buffer so that the
            # previous point remains available if we need it
            # We also directly normalize it to a decimal degree value

            # Slide the buffers
            point_buffer[0] = point_buffer[1]
            codetype_buffer[0] = codetype_buffer[1]

            # Collect next point
            code_type = xml_point.find('codeType').text
            point_buffer[1] = FloatGisPoint(GisUtil.format_decimal_degree(xml_point.find('geoLat').text),
                                          GisUtil.format_decimal_degree(xml_point.find('geoLong').text),
                                          xml_point.find('valCrc').text, code_type)

            if code_type == 'GRC':
                codetype_buffer[1] = 'GRC'
                # Nothing more to collect

            if code_type == 'RHL':
                codetype_buffer[1] = 'RHL'
                # Nothing more to collect

            if code_type == 'FNT':
                codetype_buffer[1] = 'FNT'

                # Collect the border id information
                border_uuid = xml_point.find('GbrUid').get('mid')

            if code_type == 'CCA':
                codetype_buffer[1] = 'CCA'

                arc_center = FloatGisPoint(GisUtil.format_decimal_degree(xml_point.find('geoLatArc').text),
                                           GisUtil.format_decimal_degree(xml_point.find('geoLongArc').text),
                                           xml_point.find('valCrc').text + "center", "CCA_CENTER")

                arc_radius = GisUtil.format_geo_size(
                    value=xml_point.find('valRadiusArc').text,
                    unit=xml_point.find('uomRadiusArc').text
                )

            # TODO: Refactor to make it DRY (too similar with previous code extract)
            if code_type == 'CWA':
                codetype_buffer[1] = 'CWA'

                arc_center = FloatGisPoint(GisUtil.format_decimal_degree(xml_point.find('geoLatArc').text),
                                           GisUtil.format_decimal_degree(xml_point.find('geoLongArc').text),
                                           xml_point.find('valCrc').text + "center", "CCA_CENTER")

                arc_radius = GisUtil.format_geo_size(
                    value=xml_point.find('valRadiusArc').text,
                    unit=xml_point.find('uomRadiusArc').text
                )

            # Now we implement the previous code_type
            if codetype_buffer[0] == 'GRC' or codetype_buffer[0] == 'RHL':
                # We just pile up the point
                gis_data.append(point_buffer[0])
            if codetype_buffer[0] == 'FNT':
                logger.debug('Expanding Border (FNT %s)', border_uuid)
                # We pile up the first point
                gis_data.append(point_buffer[0])
                # ... and extend with the points extracted from the border
                border_obj = aixm_source.get_border(border_uuid)
                border_points = BorderHelper.extract_border_points(border_obj, point_buffer[0], point_buffer[1])
                gis_data.extend(border_points)
                crossing = BorderCrossing(border_uuid, border_obj.text_name)
                crossing.common_points.extend(border_points)
                border_crossings.append(crossing)
                # Cleanup
                gbr_uid = None
            if codetype_buffer[0] == 'CCA':
                #logger.debug(
                #    'Expanding Arc (CCA) Center: %s, %s Radius: %s',
                #    arc_center[0], arc_center[1], str(arc_radius)
                #)
                # We pile up the first point
                gis_data.append(point_buffer[0])
                # Counter Clockwise = -1
                gis_data.extend(
                    CircleHelper.extract_arc_points(-1, arc_center, arc_radius, point_buffer[0], point_buffer[1]))

                # Cleanup
                arc_center = None
                arc_radius = None

            if codetype_buffer[0] == 'CWA':
                #logger.debug(
                #    'Expanding Arc (CWA) Center: %s, %s Radius: %s',
                #    arc_center[0], arc_center[1], str(arc_radius)
                #)
                # We pile up the first point
                gis_data.append(point_buffer[0])
                # Counter Clockwise = -1
                gis_data.extend(
                    CircleHelper.extract_arc_points(1, arc_center, arc_radius, point_buffer[0], point_buffer[1]))

                # Cleanup
                arc_center = None
                arc_radius = None

            if codetype_buffer[0] == '':
                logger.debug(
                    'This is the very first point'
                )

        # When the loop is over, we still have our last buffer point to add.
        gis_data.append(point_buffer[1])

        return gis_data, border_crossings


    @staticmethod
    def build_free_geometry_point_list_wrong(xml_point_list: list, aixm_source: AixmSource) -> tuple:
        """
        Build free geometry airspace polygon.

        :param lxml.etree.Element xml_point_list: a list of xml element representing airspace points geometry
        :param airspace.sources.AixmSource aixm_source: An instance of airspace.sources.AixmSource
        :return: a list of airspace.interfaces.GisPoint implementation
        :rtype: list
        """
        current_point = None
        gis_data = []
        border_crossings = []
        for xml_point in xml_point_list:
            previous_point = current_point
            code_type = xml_point.find('codeType').text
            current_point = FloatGisPoint(GisUtil.format_decimal_degree(xml_point.find('geoLat').text),
                                          GisUtil.format_decimal_degree(xml_point.find('geoLong').text),
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

                    arc_center = FloatGisPoint(GisUtil.format_decimal_degree(xml_point.find('geoLatArc').text),
                                               GisUtil.format_decimal_degree(xml_point.find('geoLongArc').text),
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

                    arc_center = FloatGisPoint(GisUtil.format_decimal_degree(xml_point.find('geoLatArc').text),
                                               GisUtil.format_decimal_degree(xml_point.find('geoLongArc').text),
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
    """
   An implementation of airspace.interfaces.GisPoint accepting Float values in constructor

   Attributes:
       _accuracy   The maximum amount of decimal for GPS precision (5 = 1.1m)
   """

    def __init__(self, lat: float, lon: float, crc: str, code_type: str, accuracy: int = 5) -> GisPoint:
        """

        :param float lat: Decimal latitude of the airspace.interfaces.GisPoint
        :param float lon: Decimal longitude of the airspace.interfaces.GisPoint
        :param float crc: unique code for the point. might have generated
        :param float code_type: type of point
        :param accuracy: The maximum amount of decimal for GPS precision (default : 5 = 1.1m)
        """
        super().__init__(crc, code_type, accuracy)
        self.set_lat(lat)
        self.set_lon(lon)

    def set_lon(self, lon: float) -> None:
        """
        Sets the longitude for the implemented point
        :param  Float lon: Decimal longitude of the airspace.interfaces.GisPoint
        """
        self._float_lon = GisUtil.truncate(lon, self._accuracy)
        self._dms_lon = GisUtil.dd2dms(lon, True)

    def set_lat(self, lat: float) -> None:
        """
        Sets the latitude for the implemented point
        :param  Float lat: Decimal latitude of the airspace.interfaces.GisPoint
        """
        self._float_lat = GisUtil.truncate(lat, self._accuracy)
        self._dms_lat = GisUtil.dd2dms(lat, False)

    def __str__(self) -> str:
        """
        String representation of the current point

        :rtype: str
        :return: a string representation of the point
        """
        return '[' + str(self._float_lon) + ', ' + str(self._float_lat) + ']'


class DmsGisPoint(GisPoint):
    """
    An implementation of airspace.interfaces.GisPoint accepting DMS values in constructor
    """

    def __init__(self, lat: str, lon: str, crc: str, code_type: str, accuracy: int = 5) -> GisPoint:
        """

        :param str lat: DMS latitude of the airspace.interfaces.GisPoint
        :param str lon: DMS longitude of the airspace.interfaces.GisPoint
        :param str crc: unique code for the point. might have generated
        :param str code_type: type of point
        """
        super().__init__(crc, code_type, accuracy)
        self.set_lat(lat)
        self.set_lon(lon)

    def set_lon(self, lon: str) -> None:
        """
        Sets the longitude for the implemented point
        :param  str lon: DMS longitude of the airspace.interfaces.GisPoint
        """
        self._float_lon = GisUtil.truncate(GisUtil.format_decimal_degree(lon), self._accuracy)
        self._dms_lon = GisUtil.dd2dms(GisUtil.format_decimal_degree(lon), True)

    def set_lat(self, lat: str) -> None:
        """
        Sets the latitude for the implemented point
        :param  str lat: DMS latitude of the airspace.interfaces.GisPoint
        """
        self._float_lat = GisUtil.truncate(GisUtil.format_decimal_degree(lat), self._accuracy)
        self._dms_lat = GisUtil.dd2dms(GisUtil.format_decimal_degree(lat), False)

    def __str__(self) -> str:
        """
        String representation of the current point

        :rtype: str
        :return: a string representation of the point
        """
        return '[' + str(self._dms_lon) + ', ' + str(self._dms_lat) + ']'
