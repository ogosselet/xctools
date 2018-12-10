from __future__ import absolute_import, division, print_function
from lxml import etree, objectify

from shapely.geometry import Point

import pyproj
import shapely
import re
import simplekml
import logging

logger = logging.getLogger(__name__)

geod = pyproj.Geod(ellps='WGS84')


#class Airspace(object):

#    def __init__(self):

def format_vertical_limit(code, value, unit):

    #TODO: AGL/AMSL ? Ft/FL ? ...

    return '{}-{}-{}'.format(code, value, unit)

def format_geo_size(value, unit):
     
     #TODO: cover all possible unit
     return float(value)/60

def compute_distance(geo_center, geo_point):

    dstproj = pyproj.Proj('+proj=ortho +lon_0=%f +lat_0=%f' % (geo_center[0], geo_center[1]))
    srcproj = pyproj.Proj(ellps='WGS84', proj='latlong')
    new_cx, new_cy = pyproj.transform(srcproj, dstproj, geo_center[0], geo_center[1])
    new_px, new_py = pyproj.transform(srcproj, dstproj, geo_point[0], geo_point[1])
    radius = Point(new_cx, new_cy).distance(Point(new_px, new_py))
    logger.debug('Computed radius by shapely %s', radius)
    azimuth1, azimuth2, radius2 = geod.inv(geo_center[0], geo_center[1], geo_point[0], geo_point[1])
    logger.debug('Computed radius by pyproj only %s', radius2)

def dms2dd(degree, minute, second, decimal):
    '''Degree Minute Second (Decimal) => Decimal Degree
    
    Args:
        degree ([int]): [description]
        minute ([int]): [description]
        second ([int]): [description]
        decimal ([float]): [description]
    
    Returns:
        [float]: the Decimal Degree
    '''

    return float(degree) + float(minute)/60 + float(second)/3600 + decimal/3600

def format_decimal_degree(coordinate_string):
    '''Detect a coordinate format & perform the transformation to Decimal Degree

    North Latitude & East Longitude return a positive value
    South Latitude & West Longitude return a negative value
    
    Args:
        coordinate_string ([str]): the input coordinate string that we will auto-detect
    
    Returns:
        [type]: [description]
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
            decimal = float(lat_string.group(4))
        else:
            decimal = 0

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
            decimal = float(long_string.group(4))
        else:
            decimal = 0

        return sign * dms2dd(
            degree=long_string.group(1),
            minute=long_string.group(2),
            second=long_string.group(3),
            decimal=decimal
        )

    #TODO: Raise an exception if we received a format not supported

class Airspace(object):

    def __init__(self, source, uuid):

        self.source = source
        self.uuid = uuid
        self.admin_data = None
        self.gis_data = None

         

    def parse_airspace(self):

        logger.debug('Parsing Airspace')
        self.admin_data = self.source.airspace_admin_data(self.uuid)
        self.gis_data = self.source.airspace_geometry_data(self.uuid)


    def _admin_info(self):

        pass



class AixmSource(object):
    '''Class to process Airspace information contained in an AIXM 4.5 source file

    This class should implement all the method expected by the Airspace class to
    collect all the relevant information present in the source (admin info, geo info, ...)
    '''


    def  __init__(self, filename):
        '''Initialize our AIXM Tree from a file

        Args:
            filename ([type]): [description]
        '''

        self.tree =  etree.parse(filename)
        self.airspace_mids = []
        self._border_lookup = []

        # Always store tha last GRC point processed  
        self.last_grc = None 

    #def as_string(self):
    #    return etree.tostring(self.tree)

    def list_airspace_uuid(self):
        '''List all Airspace contained in a specific source file

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


    def airspace_admin_data(self, ase_uid):

        #TODO: continue to extract all admin data of the Airspace
        #TODO: moore formating expected

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

        gis_data = []
        border_flag = False
        abd_elem = self.tree.xpath('//Abd[AbdUid[AseUid[@mid="' + ase_uid + '"]]]')
        avx_elems = abd_elem[0].xpath('Avx')

        # Loop in all avx in order
        for avx_elem in avx_elems:
            if avx_elem.xpath('codeType/text()')[0] == 'FNT':

                # We need 3 information to expand a border
                #  - the uuid of the border (gbr_uuid)
                #  - the "last" airspace point before the border (begin of border)
                #  - the "first" airspace point after the border (end of border)
                #

                gbr_uid = avx_elem.xpath('GbrUid')[0].get('mid')
                border_start = [
                    format_decimal_degree(avx_elem.xpath('geoLat/text()')[0]),
                    format_decimal_degree(avx_elem.xpath('geoLong/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ]
                border_flag=True

                gis_data.append(border_start)

                continue

            if avx_elem.xpath('codeType/text()')[0] == 'GRC' and not border_flag:
                # This is just a normal point we pile it up
                
                self.last_grc = [
                    format_decimal_degree(avx_elem.xpath('geoLat/text()')[0]),
                    format_decimal_degree(avx_elem.xpath('geoLong/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                    ]

                gis_data.append(self.last_grc)

                continue

            elif border_flag:
                # This is the first point after the border
                border_stop = ([
                    format_decimal_degree(avx_elem.xpath('geoLat/text()')[0]),
                    format_decimal_degree(avx_elem.xpath('geoLong/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ])
                border_flag = False

                # Border limit defines
                gis_data.extend(self.extract_border_points(gbr_uid, border_start, border_stop))

                # We need to add the border stop point right ? Otherwise we don't get it
                gis_data.append(border_stop)

                continue

            if avx_elem.xpath('codeType/text()')[0] == 'CCA':
                #TODO: Expand the geometry

                # The center:
                arc_center = [
                    format_decimal_degree(avx_elem.xpath('geoLatArc/text()')[0]),
                    format_decimal_degree(avx_elem.xpath('geoLongArc/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ]

                arc_point = [
                    format_decimal_degree(avx_elem.xpath('geoLat/text()')[0]),
                    format_decimal_degree(avx_elem.xpath('geoLong/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ]

                arc_radius = format_geo_size(
                    value=avx_elem.xpath('valRadiusArc/text()')[0],
                    unit=avx_elem.xpath('uomRadiusArc/text()')[0]
                )

                logger.debug('Starting to compute an arc:')
                logger.debug('    center: %s %s', arc_center[0], arc_center[1])
                logger.debug('    radius: %s', arc_radius)

                # Naive Circle Approach
                points = self._circle_experiment((arc_center[0], arc_center[1]), arc_radius)
                for point in points:
                    gis_data.append([point[0], point[1]])

                compute_distance((arc_center[1], arc_center[0]),(arc_point[1], arc_point[0]))
                compute_distance(
                    (arc_center[1], arc_center[0]),
                    (format_decimal_degree('0045550E'), format_decimal_degree('502319N') )
                )

                pass
                #gis_data.append([
                #    'C',
                #    'C',
                #    'A'
                #])

        return gis_data

    def extract_border_points(self, gbr_uid, border_start, border_stop):

        logger.debug('Extracting border <GbrUid mid=%s>', gbr_uid)

        self._prepare_border_lookup(gbr_uid)
        # We will create a structure to lookup our potential points
        
        # Finding the closest surrounding points
        # Now we need to do the clever extraction
        crc_start = self._get_crc_around_border_point(latitude=border_start[0], longitude=border_start[1])
        crc_stop = self._get_crc_around_border_point(latitude=border_stop[0], longitude=border_stop[1])

        index_start = self._get_border_point_index(crc_start)
        index_stop = self._get_border_point_index(crc_stop)

        return self._get_border_points(index_start, index_stop)

    def _prepare_border_lookup(self, gbr_uid):

        # The <Gbr>
        gbr_elem = self.tree.xpath('//Gbr[GbrUid[@mid="' + gbr_uid + '"]]')

        # Find all <Gbv>
        gbv_elems = gbr_elem[0].xpath('Gbv')

        for gbv_elem in gbv_elems:
            # We need to be sure the points are coded in decimal degree
            # If not, we transform it
            geo_lat = format_decimal_degree(gbv_elem.xpath('geoLat/text()')[0])
            geo_long = format_decimal_degree(gbv_elem.xpath('geoLong/text()')[0])
            val_crc = gbv_elem.xpath('valCrc/text()')[0]
            self._border_lookup.append([geo_lat, geo_long, val_crc])
    
    def _get_crc_around_border_point(self, latitude, longitude):

        #print('Lat: {} - Long:{}'.format(geo_lat, geo_long))
        # Iterate over all the border points skipping the first one
        logger.debug('Finding position on border for Lat:%s / Long:%s', latitude, longitude)
        min_distance = float(1000000000000)
        crc_left = ''
        crc_right = ''
        for i in range(len(self._border_lookup)-1):
            geo_lat_1 = self._border_lookup[i][0]
            geo_long_1 = self._border_lookup[i][1]
            #print('Lat: {} - Long:{}'.format(geo_lat_1, geo_long_1))
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
                #print('CRC Left: {} - CRC Right: {}'.format(crc_left, crc_right))
                #print('Lat: {} - Long:{}'.format(geo_lat_1, geo_long_1))
                #print(min_distance)

        return (crc_left, crc_right)

    def _get_border_point_index(self, val_crc):

        #TODO: There is probably a more pythonic way to perform this lookup in a
        #TODO: list !
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
        '''Get the subset of the border point in the good order
        
        Args:
            index_start ([tupple]): the index of the 2 points around our first border point
            index_stop ([type]): the index of the 2 points around our last border point
        '''

        # Remember tht index_ are still tupple for now.
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

    def _circle_experiment(self, center_point, radius):

        circle = Point(center_point[0], center_point[1]).buffer(radius)
        print(circle)
        circle_coord = circle.exterior.coords
        return circle_coord
        
#    def extract_gbv(self, gbr_uid, first_index, last_index, reverse_order=False):
#
#        tmp = []
#
#       # The <Gbr>
#        gbr_elem = self.tree.xpath('//Gbr[GbrUid[@mid="' + gbr_uid + '"]]')
#        # Find all <Gbv>
#        gbv_elems = gbr_elem[0].xpath('Gbv')
#        print(len(gbv_elems))
#        print(first_index)
#        print(gbv_elems[first_index].xpath('valCrc/text()'))
#        print(last_index)
#        #return gbv_elems[10:20]
#        if reverse_order:
#            return list(reversed(gbv_elems[first_index:last_index+1]))
#        else:
#            return gbv_elems[first_index:last_index+1]




#    def get_all_airspace_elements(self, ase_uid):
#
#        out = []
#
#        # The <Ase>
#        ase_elem = self.tree.xpath('//Ase[AseUid[@mid="' + ase_uid + '"]]')
#        out.extend(ase_elem)

#        # The <Abd>
#        abd_elem = self.tree.xpath('//Abd[AbdUid[AseUid[@mid="' + ase_uid + '"]]]')
#        out.extend(abd_elem)
#
#        return out


if __name__ == '__main__':

    # We run our demo in DEBUG mode
    logging.basicConfig(level=logging.DEBUG)

    # Inspect is maybe better to build this type of string ?
    logger.info('<-- Module %s demo code -->', __file__)

    # Open an AIXM 4.5 SRC
    aixm_source = AixmSource('downloads/EBBU/ebbu_4.5_bis.xml')

    # List all Airpaces present in the source
    all_airspaces = aixm_source.list_airspace_uuid()

    # Work on a specific Airspace
    airspace = Airspace(aixm_source, str(100760256))
    airspace.parse_airspace()

    # Produce a KML
    kml=simplekml.Kml()
    for nbr, gbv in enumerate(airspace.gis_data):
        kml.newpoint(
            name='gbv-{}'.format(nbr),
            coords=[(gbv[1], gbv[0])]
        )
        print('Lat: {}, Lon: {}'.format(gbv[1], gbv[0]))
    kml.save('test_border.kml')

    #test_circle = aixm_source._circle_experiment((100, 150), 20)
    #print(test_circle)

