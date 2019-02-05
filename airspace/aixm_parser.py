from __future__ import absolute_import, division, print_function

import re
import logging

import pyproj
import simplekml

from lxml import etree
from shapely.geometry import Point
from shapely.ops import transform

logger = logging.getLogger(__name__)

geod = pyproj.Geod(ellps='WGS84')

FREE_GEOM = 1
CIRCLE_GEOM = 2


class AixmSourceError(Exception):
    '''Exception class building a common message format including AIXM info

    Args:
        Exception (object): Exception as superclass

    '''

    def __init__(self, aixm_source, msg=None):
        '''Init the superclass "Exception" string

        Args:
            aixm_source ([AixmSource]): the AixmSource object where the exception was triggered
            msg ([str], optional): Defaults to None. The contextual message of the Exception
        '''

        if msg is None:
            # Set some default useful error message
            msg = 'unexpected error'
        exc_msg = 'AIXM {}: {}'.format(aixm_source.filename, msg)

        super(AixmSourceError, self).__init__(exc_msg)
        self.aixm_source = aixm_source


class AirspaceGeomUnknown(AixmSourceError):
    '''Exception raised when a AIXM decoding error is detected

    Args:
        AixmSourceError (Exception): AixmSourceError as superclass
    '''

    def __init__(self, aixm_source, msg=None):
        '''Init the superclass AixmSourceError message

        Args:
            aixm_source ([AixmSource]): the AixmSource object where the exception was triggered
            msg ([str], optional): Defaults to None (replaced by a generic message).
                The contextual message of the Exception
        '''

        if msg is None:
            msg = 'unknown geometry'
        super(AirspaceGeomUnknown, self).__init__(aixm_source, msg)

def format_vertical_limit(code, value, unit):


    #TODO: AGL/AMSL ? Ft/FL ? ...
    return '{}-{}-{}'.format(code, value, unit)

def format_geo_size(value, unit):

    #TODO: cover all possible unit
    if unit == "NM":
        return float(value)*1852
    if unit == "KM":
        return float(value)*1000

def compute_distance(geo_pt1, geo_pt2):
    '''Compute great circle distance between 2 points

    TODO: Not really used but we might reuse it to compute the "mean" circle radius

    Args:
        geo_center ([latitude, longitude]): the geo coordinates of the first point
        geo_point ([latitude, longitude]): the geo coordinates of the second point
    '''

    dstproj = pyproj.Proj('+proj=ortho +lon_0=%f +lat_0=%f' % (geo_pt1[0], geo_pt2[1]))
    srcproj = pyproj.Proj(ellps='WGS84', proj='latlong')
    new_cx, new_cy = pyproj.transform(srcproj, dstproj, geo_pt1[0], geo_pt1[1])
    new_px, new_py = pyproj.transform(srcproj, dstproj, geo_pt2[0], geo_pt2[1])
    radius = Point(new_cx, new_cy).distance(Point(new_px, new_py))
    logger.debug('Computed radius by shapely %s', radius)
    azimuth1, azimuth2, radius2 = geod.inv(geo_pt1[0], geo_pt1[1], geo_pt2[0], geo_pt2[1])
    logger.debug('Computed radius by pyproj only %s', radius2)

def dms2dd(degree, minute, second, decimal=0):
    '''Degree Minute Second (Decimal) => Decimal Degree

    Args:
        degree ([int]): number or string repr. of integer
        minute ([int]): number or string repr. of integer
        second ([int]): number or string repr. of integer
        decimal ([float]): optional decimal of seconds in the form 0.xxxxx

    Returns:
        [float]: the Decimal Degree
    '''

    return float(degree) + float(minute)/60 + float(second)/3600 + float(decimal)/3600

def format_decimal_degree(coordinate_string):
    '''Detect a coordinate format & perform the transformation to Decimal Degree

    Works for string representation of Latitude or Longitude

    North Latitude & East Longitude return a positive value
    South Latitude & West Longitude return a negative value

    Args:
        coordinate_string ([str]): the input coordinate string that we will auto-detect

    Returns:
        [float]: a decimal degree coordinate value
    '''

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

        return sign * dms2dd(
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

        return sign * dms2dd(
            degree=long_string.group(1),
            minute=long_string.group(2),
            second=long_string.group(3),
            decimal=decimal
        )
    #TODO: Raise an exception if we received a format not supported


class GisPoint(object):

    __lat = None
    __long = None
    __crc = None
    __precision = 5

    def __init__(self,lat,lon,crc):
        self.set_lon(lon)
        self.set_lat(lat)
        self.set_crc(crc)

    def truncate(self,f, n):
        '''Truncates/pads a float f to n decimal places without rounding'''
        s = '{}'.format(f)
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        return '.'.join([i, (d + '0' * n)[:n]])

    def set_lon(self,lon):

        self.lon = float(self.truncate(lon,self.__precision))

    def get_lon(self):
        return self.lon

    def set_lat(self,lat):
        self.__lat = float(self.truncate(lat,self.__precision))

    def get_lat(self):
        return self.__lat

    def set_crc(self,crc):
        self.__crc =crc

    def get_crc(self):
        return self.__crc

    def __str__(self):
        return '[' + str(self.lon) +', ' + str(self.__lat) + ', ' + str(self.__crc) + ']'

    # Now you can compare if 2 GisPoint are equals (== or assertEqual() )
    # if we implement __lt__, __le__, __gt__ and __ge__ GisPoint could be sortable (don't know if it is use full)
    def __eq__(self,other):

        return (self.get_lon() == other.get_lon())and(self.get_lat()==other.get_lat())and (self.get_crc() == other.get_crc())

class GisDataFactory(object):


    @staticmethod
    def parse_element(self,xml_element,ase_uid):
        gis_data = []
        if xml_element[0].xpath('Circle'):
            # do stuffs with circles not sure what is returned in that case
            logger.debug('Circle geometry detected')
        elif xml_element[0].xpath('Avx'):
            #do stuff with Avx
            logger.debug('Free geometry detected')
            for avx_elem in xml_element[0].xpath('Avx'):
                # Willingly over simplified for code clarity (this is a proof of concept before optional rewrite)
                if avx_elem.xpath('codeType/text()')[0] == 'GRC':
                    gis_point = GisPoint(format_decimal_degree(avx_elem.xpath('geoLat/text()')[0]),
                        format_decimal_degree(avx_elem.xpath('geoLong/text()')[0]),
                        avx_elem.xpath('valCrc/text()')[0])
                    gis_data.append(gis_point)
        else:
            raise AirspaceGeomUnknown(self, ase_uid)
        return gis_data

class Airspace(object):
    '''Airspace Interface Abstraction Class

    Implement a common set of Airspace method independant from the Source of the Airspace information
    '''


    def __init__(self, source, uuid):
        '''Init Method creating a new XCTools Airspace object

        Args:
            source ([object]): a supported Airspace[description]
            uuid ([string]): a unique id of the source for the file we are trying to extract
        '''

        self.source = source
        self.uuid = uuid
        self.admin_data = None
        self.gis_data = None

    def parse_airspace(self):
        '''Execute the parsing of the Airspace to extract Admin & GIS data
        '''

        logger.debug('Parsing Airspace')
        self.admin_data = self.source.airspace_admin_data(self.uuid)
        self.gis_data = self.source.airspace_geometry_data(self.uuid)

class AixmSource(object):
    '''Class to process Airspace information contained in an AIXM 4.5 source file

    This class should implement all the method expected by the Airspace class to
    collect all the relevant information present in the source (admin info, geo info, ...)
    and normalize the return data to our XCTools format
    '''

    def  __init__(self, filename):
        '''Initialize the AIXM source

        Args:
            filename ([type]): the file system file containing the AIXM 4.5 Airspace Informations
        '''

        self.filename = filename
        self.tree =  etree.parse(self.filename)
        self.airspace_mids = []
        self._border_lookup = []
        self._arc_lookup = []

        # A "sliding" buffer to store the last GRC points
        self.grc_buf = ['','']

    def list_airspace_uuid(self):
        '''List all Airspace contained in the specific source file

        Interface method that needs to be implemented for any source

        Returns:
            list: list of dictionary {'uuid': file_specific_uuid , 'name': airspace_name }
                  The 'name' is provided for convenience or to be used as a natural key
                  across multiple AIXM file if 'uuid' is not maintained (time or source)
        '''

        tmp = []

        for ase_uid in self.tree.xpath('//AseUid'):
            tmp.append(
                {
                    'uuid': ase_uid.get('mid'),
                    'name': ase_uid.xpath('codeId/text()')[0]
                }
            )

        return tmp

#    def list_code_type(self):
#
#        for avx in self.tree.xpath('//Abd/Avx'):
#            print('CODE: {}'.format(avx.xpath('codeType/text()')[0]))

    def airspace_admin_data(self, ase_uid):
        '''Extract & normalize the Airspace Admin data

        Args:
            ase_uid ([string]): The UUID ot the Airspace

        Returns:
            [dict]: the Airspace Admin data as a dictionary
        '''

        #TODO: continue to extract all admin data of the Airspace
        #TODO: more formating expected

        # Parse admin data
        admin_data = {}
        ase_elem = self.tree.xpath('//Ase[AseUid[@mid="' + ase_uid + '"]]')
        admin_data['codeId'] = ase_elem[0].xpath('AseUid/codeId/text()')[0]
        admin_data['txtName'] = ase_elem[0].xpath('AseUid/codeId/text()')[0]
        admin_data['upper'] = format_vertical_limit(
            code=ase_elem[0].xpath('codeDistVerUpper/text()')[0],
            value=ase_elem[0].xpath('valDistVerUpper/text()')[0],
            unit=ase_elem[0].xpath('uomDistVerUpper/text()')[0]
        )

        # This method should return the data in the expected format expected by the Airspace
        return admin_data

    def airspace_geometry_data(self, ase_uid):
        '''Extract & normalize the Airspace GIS data

        TODO: cover the creation of the polygon in WKT to make the consumption easier

        Args:
            ase_uid ([string]): The UUID ot the Airspace

        Raises:
            AirspaceGeomUnknown: Exception raised when the GIS data extraction method is not known

        Returns:
            [list]: the Airspace GIS data as a list of coordinates that can be used to create a "Polygon"
        '''


        abd_elem = self.tree.xpath('//Abd[AbdUid[AseUid[@mid="' + ase_uid + '"]]]')
        # TODO: I would return GisDataFactory.parse_element(abd_elem, ase_uid) here => end of method
        if abd_elem[0].xpath('Avx'):
            print(abd_elem[0].xpath('Avx'))
            logger.debug('Free geometry detected')
            # TODO: L.R: slows down everything better to pass the xml element rather than parsing again (see sub method call)
            return self._airspace_free_geometry(ase_uid)

        if abd_elem[0].xpath('Circle'):
            logger.debug('Circle geometry detected')
            # TODO: L.R: slows down everything better to pass the xml element rather than parsing again (see sub method call)
            return self._airspace_circle_geometry(ase_uid)

        raise AirspaceGeomUnknown(self, ase_uid)

    def _airspace_circle_geometry(self, ase_uid):
        '''Create a polygon for a Circle geometry

        Args:
            ase_uid ([string]): The UUID ot the Airspace

        Returns:
            [list]: a list of coordinates that can be used to create a "Polygon"
        '''

        abd_elem = self.tree.xpath('//Abd[AbdUid[AseUid[@mid="' + ase_uid + '"]]]')
        circle_elem = abd_elem[0].xpath('Circle')[0]

        # Collect the center & the radius of the Circle
        arc_center = [
            format_decimal_degree(circle_elem.xpath('geoLatCen/text()')[0]),
            format_decimal_degree(circle_elem.xpath('geoLongCen/text()')[0]),
            circle_elem.xpath('valCrc/text()')[0]]

        # Collect the radius
        arc_radius = format_geo_size(
            value=circle_elem.xpath('valRadius/text()')[0],
            unit=circle_elem.xpath('uomRadius/text()')[0])

        self._prepare_arc_lookup((arc_center[0], arc_center[1]), arc_radius)
        return self._arc_lookup

    # TODO: that looks like a Factory pattern : https://www.tutorialspoint.com/design_pattern/factory_pattern.htm
    # TODO : see GisDataFactory class for implementation idea
    def _airspace_free_geometry(self, ase_uid):
        '''Create a polygon for a Free geometry

        Free geometry are made of points, border points, arc of circle

        Args:
            ase_uid ([string]): The UUID ot the Airspace

        Returns:
            [list]: a list of coordinates that can be used to create a "Polygon"
        '''

        grc_buffer = ['', '']
        avx_function_buffer = ['', '']
        gis_data = []

        abd_elem = self.tree.xpath('//Abd[AbdUid[AseUid[@mid="' + ase_uid + '"]]]')
        avx_elems = abd_elem[0].xpath('Avx')
        # Loop in all avx in order
        for avx_elem in avx_elems:
            # In an AVX, there is always a reference to a point
            # We will store this point in a sliding buffer so that the
            # previous point remains available if we need it
            # We also directly normalize it to a decimal degree value

            # Slide the buffers
            grc_buffer[0] = grc_buffer[1]
            avx_function_buffer[0] = avx_function_buffer[1]

            # Collect next point
            grc_buffer[1] = [
                    format_decimal_degree(avx_elem.xpath('geoLat/text()')[0]),
                    format_decimal_degree(avx_elem.xpath('geoLong/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ]

            if avx_elem.xpath('codeType/text()')[0] == 'GRC':
                avx_function_buffer[1] = 'GRC'
                # Nothing more to collect

            if avx_elem.xpath('codeType/text()')[0] == 'RHL':
                avx_function_buffer[1] = 'RHL'
                # Nothing more to collect

            if avx_elem.xpath('codeType/text()')[0] == 'FNT':
                avx_function_buffer[1] = 'FNT'

                # Collect the border id information
                gbr_uid = avx_elem.xpath('GbrUid')[0].get('mid')

            if avx_elem.xpath('codeType/text()')[0] == 'CCA':
                avx_function_buffer[1] = 'CCA'

                # Collect the center & the radius of the Circle Arc
                arc_center = [
                    format_decimal_degree(avx_elem.xpath('geoLatArc/text()')[0]),
                    format_decimal_degree(avx_elem.xpath('geoLongArc/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ]

                arc_radius = format_geo_size(
                    value=avx_elem.xpath('valRadiusArc/text()')[0],
                    unit=avx_elem.xpath('uomRadiusArc/text()')[0]
                )
            #TODO: Refactor to make it DRY (too similar with previous code extract)
            if avx_elem.xpath('codeType/text()')[0] == 'CWA':
                avx_function_buffer[1] = 'CWA'

                # Collect the center & the radius of the Circle Arc
                arc_center = [
                    format_decimal_degree(avx_elem.xpath('geoLatArc/text()')[0]),
                    format_decimal_degree(avx_elem.xpath('geoLongArc/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ]

                arc_radius = format_geo_size(
                    value=avx_elem.xpath('valRadiusArc/text()')[0],
                    unit=avx_elem.xpath('uomRadiusArc/text()')[0]
                )

            # Now we implement the previous avx_function
            if avx_function_buffer[0] == 'GRC' or avx_function_buffer[0] == 'RHL' :
                # We just pile up the point
                gis_data.append(grc_buffer[0])
            if avx_function_buffer[0] == 'FNT':
                logger.debug('Expanding Border (FNT %s)', gbr_uid)
                # We pile up the first point
                gis_data.append(grc_buffer[0])
                # ... and extend with the points extracted from the border
                gis_data.extend(self.extract_border_points(gbr_uid, grc_buffer[0], grc_buffer[1]))
                # Cleanup
                gbr_uid = None
            if avx_function_buffer[0] == 'CCA':
                logger.debug(
                    'Expanding Arc (CCA) Center: %s, %s Radius: %s',
                    arc_center[0], arc_center[1], arc_radius
                    )

                # We pile up the first point
                gis_data.append(grc_buffer[0])

                # Counter Clockwise = -1
                gis_data.extend(self.extract_arc_points(-1, arc_center, arc_radius, grc_buffer[0], grc_buffer[1]))

                # Cleanup
                arc_center = None
                arc_radius = None

            if avx_function_buffer[0] == 'CWA':
                logger.debug(
                    'Expanding Arc (CWA) Center: %s, %s Radius: %s',
                    arc_center[0], arc_center[1], arc_radius
                    )
                # We pile up the first point
                gis_data.append(grc_buffer[0])

                # Clockwise = 1
                gis_data.extend(self.extract_arc_points(1, arc_center, arc_radius, grc_buffer[0], grc_buffer[1]))

                # Cleanup
                arc_center = None
                arc_radius = None

            if avx_function_buffer[0] == '':
                logger.debug(
                    'This is the very first point'
                )

        # When the loop is over, we still have our last buffer point to add.
        gis_data.append(grc_buffer[1])

        return gis_data

    def extract_arc_points(self, direction, arc_center, arc_radius, arc_start, arc_stop):
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

        # Buffer the full circle in a data structure that we will lookup to isolate or arc points
        self._prepare_arc_lookup(arc_center, arc_radius)

        # Finding the closest surrounding points around the start/stop points of our Arc on the Circle
        # idx_ are tupples of point index on the circle
        idx_start = self._get_idx_around_arc_point(latitude=arc_start[0], longitude=arc_start[1])
        idx_stop = self._get_idx_around_arc_point(latitude=arc_stop[0], longitude=arc_stop[1])

        # The actual extraction of the points
        return self._get_arc_points(direction, idx_start, idx_stop)


    def _prepare_arc_lookup(self, arc_center, arc_radius):
        '''Circle points indexed "lookup" structure

        Args:
            arc_center ([lat, long]): the The geo coord. (lat/long) of the Circle center
            arc_radius ([float]): the radius of the Circle
        '''

        # Cleanup to remove any previous circle "lookup" data from a previous circle
        logger.debug('Cleaning up the arc lookup structure')
        self._arc_lookup = []
        # Reprojected Circle (v3 because I tried several approach to get a proper circle drawn on a sphere)
        points = self._create_circle((arc_center[0], arc_center[1]), arc_radius)

        for i, point in enumerate(points):
            print(point)
            self._arc_lookup.append([point[1],point[0], i])

    def _get_idx_around_arc_point(self, latitude, longitude):
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
        for i in range(len(self._arc_lookup)-1):
            geo_lat_1 = self._arc_lookup[i][0]
            geo_long_1 = self._arc_lookup[i][1]
            geo_lat_2 = self._arc_lookup[i+1][0]
            geo_long_2 = self._arc_lookup[i+1][1]

            # Compute the distance
            distance = (latitude - geo_lat_1)**2 + \
                    (longitude - geo_long_1)**2 + \
                    (geo_lat_2 - latitude)**2 + \
                    (geo_long_2 - longitude)**2

            # Looking up the minimum 
            if distance < min_distance:
                min_distance = distance
                idx_left = self._arc_lookup[i][2]
                idx_right = self._arc_lookup[i+1][2]

        return (idx_left, idx_right)

    def _get_arc_points(self, direction, idx_start, idx_stop):
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
            return self._arc_lookup[start:stop]

        if direction == 1 and (idx_start[0] > idx_stop[0]):
            # We need to pass over 0

            # There is 2 extraction
            #     from max(idx_start) to the end
            start = max(idx_start)
            start_list = self._arc_lookup[start:]
            #     from 0 to min(idx_stop) + 1
            stop = min(idx_stop) + 1
            end_list = self._arc_lookup[0:stop]
            logger.debug('Extracting in CW direction from %s to %s', start, stop)
            return start_list + end_list

        # Counter Clockwise
        if direction == -1 and (idx_start[0] < idx_stop[0]):
            # We can just extract the points
            start = min(idx_start) + 1
            stop = max(idx_stop)
            return list(reversed(self._arc_lookup[0:start])) + list(reversed(self._arc_lookup[stop:]))

        if direction == -1 and (idx_start[0] > idx_stop[0]):
            # We need to pass over 0

            # There is 2 extraction
            #     from max(idx_start) to the end
            start = max(idx_stop)
            stop = min(idx_start)+1
            return list(reversed(self._arc_lookup[start:stop]))

    def extract_border_points(self, gbr_uid, border_start, border_stop):
        '''Get the subset of the relevant border point betwwen a start/stop border points
        
        Similar to the circle case, the border POI are close from the border but will
        most likely not exist as a border points in the AIXM source

        Args:
            gbr_uid ([string]): The uuid of the relevant border information discovered in the source
            border_start ([lat, long]): the first known point on the border 
            border_stop ([lat, long]): the last known point on the border
        
        Returns:
            [list]: a list of coordinates that can be used to create an important line of the Airspace polygon (i.e the border)
        '''

        logger.debug('Extracting border <GbrUid mid=%s>', gbr_uid)

        # We will create a structure to lookup our potential points
        self._prepare_border_lookup(gbr_uid)

        # Finding the closest surrounding points
        # Now we need to do the clever extraction
        crc_start = self._get_crc_around_border_point(latitude=border_start[0], longitude=border_start[1])
        crc_stop = self._get_crc_around_border_point(latitude=border_stop[0], longitude=border_stop[1])

        index_start = self._get_border_point_index(crc_start)
        index_stop = self._get_border_point_index(crc_stop)

        return self._get_border_points(index_start, index_stop)

    def _prepare_border_lookup(self, gbr_uid):
        '''Border points indexed "lookup" structure

        Args:
            gbr_uid ([string]): the UUID of the specific border segment in the source
        '''

        # The <Gbr>
        gbr_elem = self.tree.xpath('//Gbr[GbrUid[@mid="' + gbr_uid + '"]]')

        # Find all <Gbv>
        gbv_elems = gbr_elem[0].xpath('Gbv')

        for gbv_elem in gbv_elems:
            # We need to be sure the points are coded in decimal degree
            # If not, we transform them
            geo_lat = format_decimal_degree(gbv_elem.xpath('geoLat/text()')[0])
            geo_long = format_decimal_degree(gbv_elem.xpath('geoLong/text()')[0])
            val_crc = gbv_elem.xpath('valCrc/text()')[0]
            self._border_lookup.append([geo_lat, geo_long, val_crc])

    def _get_crc_around_border_point(self, latitude, longitude):
        '''Define the CRC of the 2 border points that are the closest from a POI (lat, long).

        The POI is on or very close from the border.
        We measure the distance between 2 point and our POI as follow using Pythagore

          - sqr(distance) = sqr(delta_lat) + sqr(delta_long)

        We compute a cumulated distance by summing up the 2 sqr(distance)

        The 2 consecutive border points minimizing this cumulated distance are the interesting
        point of the border.

        The main difference with the "Circle" equivalent method is that we use in this case
        the CRC value present on each and every border point as "index" lookup value for the extraction

        TODO: DRY Circle/Border methods that are at the end very similar !

        Args:
            latitude ([float]): Geo Lat. in decimal degree of the POI we want to locate on the circle
            longitude ([float]): Geo Long. in decimal degree of the POI we want to locate on the circle

        Returns:
            [tupple]: the 2 CRC index of the border points surrounding our POI
        '''

        # Iterate over all the border points skipping the first one
        logger.debug('Finding position on border for Lat:%s / Long:%s', latitude, longitude)
        min_distance = float(1000000000000)
        crc_left = ''
        crc_right = ''
        for i in range(len(self._border_lookup)-1):
            geo_lat_1 = self._border_lookup[i][0]
            geo_long_1 = self._border_lookup[i][1]
            geo_lat_2 = self._border_lookup[i+1][0]
            geo_long_2 = self._border_lookup[i+1][1]

            distance = (latitude - geo_lat_1)**2 + \
                    (longitude - geo_long_1)**2 + \
                    (geo_lat_2 - latitude)**2 + \
                    (geo_long_2 - longitude)**2

            if distance < min_distance:
                min_distance = distance
                crc_left = self._border_lookup[i][2]
                crc_right = self._border_lookup[i+1][2]

        return (crc_left, crc_right)

    def _get_border_point_index(self, val_crc):
        '''Lookup the index of the border points based on the CRC value of the points
        
        TODO: There is probably a more pythonic way to perform this lookup in a list

        Args:
            val_crc ([tupple]): the 2 CRCs of consecutive border points
        
        Returns:
            [tuple]: the index value of the border points in our lookup structure 
        '''

        for index, border_point in enumerate(self._border_lookup):
            if border_point[2] == val_crc[0]:
                index_left = index
                break
        for index, border_point in enumerate(self._border_lookup):
            if border_point[2] == val_crc[1]:
                index_right = index
                break
        return (index_left, index_right)

    def _get_border_points(self, index_start, index_stop):
        '''Extract the subset of the border points in the good direction

        Args:
            index_start ([tupple]): the index of the 2 points around our first border point
            index_stop ([tupple]): the index of the 2 points around our last border point
        '''

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
            return self._border_lookup[start:stop]
        else:
            return list(reversed(self._border_lookup[stop:start]))

    def _create_circle(self, center_point, radius):
        '''Create a circle on Earth 

        Circle drawn in normal Cartesian geometry by shapely becomes Ellipsoid on Earth

        It is necessary to introduce a concept of projection   
        
        Args:
            center_point ([type]): [description]
            radius ([type]): [description]
        '''


        logger.debug('Circle Creation')
        logger.debug('Center Lat: %s Long: %s', center_point[0], center_point[1])

        lat, lon = center_point

        AEQD = pyproj.Proj(proj='aeqd', lat_0=lat, lon_0=lon, x_0=lon, y_0=lat)
        WGS84 = pyproj.Proj(init='epsg:4326')

        # transform the given lat-long onto the flat AEQD plane
        tx_lon, tx_lat = pyproj.transform(WGS84, AEQD, lon, lat)
        circle = Point(tx_lat, tx_lon).buffer(radius)

        def inverse_tx(x, y, z=None):
            x, y = pyproj.transform(AEQD, WGS84, x, y)
            return (x, y)

        # inverse projection from AEQD to EPSG4326-WGS84
        projected_circle = transform(inverse_tx, circle)

        projected_circle_points = projected_circle.exterior.coords
        #for i, projected_circle_point in enumerate(projected_circle_points):
        #    print('{} {}'.format(i, projected_circle_point))
        return projected_circle_points

if __name__ == '__main__':

    # We run our demo in DEBUG mode
    logging.basicConfig(level=logging.DEBUG)

    # Inspect is maybe better to build this type of string ?
    logger.info('<-- Module %s demo code -->', __file__)

    # Open an AIXM 4.5 SRC
    aixm_source = AixmSource('./downloads/EBBU/ebbu_4.5.xml')

    # List all Airpaces present in the source
    all_airspaces = aixm_source.list_airspace_uuid()

    # CodeType
    # all_codetype = aixm_source.list_code_type()

    # Work on a specific Airspace

    # EBD26 - OK (FNT & 1 CCA)
    #name = 'EBD26'
    #airspace = Airspace(aixm_source, str(100760256))

    # CTR ELLX - OK (2 CWA)
    # name = 'ELLX'
    # airspace = Airspace(aixm_source, str(84915550))

    # EHMCG1 - OK (RHL & FNT)
    # name = 'EHMCG1'
    # airspace = Airspace(aixm_source, str(232804194))

    # EBBE1A
    #name = 'EBBE1A'
    #airspace = Airspace(aixm_source, str(101002747038897))

    # A Circle Geometry
    name = 'EBR28'
    airspace = Airspace(aixm_source, str(400001601922575))

    airspace.parse_airspace()


    # Produce a KML
    logger.debug('Producing a KML Polygon')
    kml = simplekml.Kml()
    pol = kml.newpolygon(name=name)
    pol.style.linestyle.color = simplekml.Color.red
    pol.style.linestyle.width = 1
    pol.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.red)
    outerboundaryis = []
    for gbv in airspace.gis_data:
        outerboundaryis.append((gbv[1], gbv[0]))
    # Close the polygon
    outerboundaryis.append((airspace.gis_data[0][1], airspace.gis_data[0][0]))
    pol.outerboundaryis = outerboundaryis
    print(outerboundaryis)

    #    kml.newpoint(
    #        name='gbv-{}'.format(nbr),
    #        coords=[(gbv[1], gbv[0])]
    #    )
    #    print('Lat: {}, Lon: {}'.format(gbv[1], gbv[0]))
    kml.save('{}.kml'.format(name))

    #test_circle = aixm_source._circle_experiment((100, 150), 20)
    #print(test_circle)

