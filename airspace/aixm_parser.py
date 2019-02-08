from __future__ import absolute_import, division, print_function

import logging

import lxml
import pyproj
import simplekml
from shapely.geometry import Point
from shapely.ops import transform

from .exceptions import AirspaceGeomUnknown
from .geometry import GisUtil

logger = logging.getLogger(__name__)

geod = pyproj.Geod(ellps='WGS84')

FREE_GEOM = 1
CIRCLE_GEOM = 2



class Airspace(object):
    """Airspace Interface Abstraction Class

    Implement a common set of Airspace method independant from the Source of the Airspace information
    """


    def __init__(self, source, uuid):
        """Init Method creating a new XCTools Airspace object

        Args:
            source ([object]): a supported Airspace[description]
            uuid ([string]): a unique id of the source for the file we are trying to extract
        """

        self.source = source
        self.uuid = uuid
        self.admin_data = None
        self.gis_data = None

    def parse_airspace(self):
        """Execute the parsing of the Airspace to extract Admin & GIS data
        """

        logger.debug('Parsing Airspace')
        self.admin_data = self.source.airspace_admin_data(self.uuid)
        self.gis_data = self.source.airspace_geometry_data(self.uuid)

class AixmSource(object):
    """Class to process Airspace information contained in an AIXM 4.5 source file

    This class should implement all the method expected by the Airspace class to
    collect all the relevant information present in the source (admin info, geo info, ...)
    and normalize the return data to our XCTools format
    """

    def  __init__(self, filename):
        """Initialize the AIXM source

        Args:
            filename ([type]): the file system file containing the AIXM 4.5 Airspace Informations
        """

        self.filename = filename
        self.tree = lxml.etree.parse(self.filename)
        self.airspace_mids = []
        self._border_lookup = []
        self._arc_lookup = []

        # A "sliding" buffer to store the last GRC points
        self.grc_buf = ['','']

    def list_airspace_uuid(self):
        """List all Airspace contained in the specific source file

        Interface method that needs to be implemented for any source

        Returns:
            list: list of dictionary {'uuid': file_specific_uuid , 'name': airspace_name }
                  The 'name' is provided for convenience or to be used as a natural key
                  across multiple AIXM file if 'uuid' is not maintained (time or source)
        """

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
        """Extract & normalize the Airspace Admin data

        Args:
            ase_uid ([string]): The UUID ot the Airspace

        Returns:
            [dict]: the Airspace Admin data as a dictionary
        """

        #TODO: continue to extract all admin data of the Airspace
        #TODO: more formating expected

        # Parse admin data
        admin_data = {}
        ase_elem = self.tree.xpath('//Ase[AseUid[@mid="' + ase_uid + '"]]')
        admin_data['codeId'] = ase_elem[0].xpath('AseUid/codeId/text()')[0]
        admin_data['txtName'] = ase_elem[0].xpath('AseUid/codeId/text()')[0]
        admin_data['upper'] = GisUtil.format_vertical_limit(
            code=ase_elem[0].xpath('codeDistVerUpper/text()')[0],
            value=ase_elem[0].xpath('valDistVerUpper/text()')[0],
            unit=ase_elem[0].xpath('uomDistVerUpper/text()')[0]
        )

        # This method should return the data in the expected format expected by the Airspace
        return admin_data

    def airspace_geometry_data(self, ase_uid):
        """Extract & normalize the Airspace GIS data

        TODO: cover the creation of the polygon in WKT to make the consumption easier

        Args:
            ase_uid ([string]): The UUID ot the Airspace

        Raises:
            AirspaceGeomUnknown: Exception raised when the GIS data extraction method is not known

        Returns:
            [list]: the Airspace GIS data as a list of coordinates that can be used to create a "Polygon"
        """


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
        """Create a polygon for a Circle geometry

        Args:
            ase_uid ([string]): The UUID ot the Airspace

        Returns:
            [list]: a list of coordinates that can be used to create a "Polygon"
        """

        abd_elem = self.tree.xpath('//Abd[AbdUid[AseUid[@mid="' + ase_uid + '"]]]')
        circle_elem = abd_elem[0].xpath('Circle')[0]

        # Collect the center & the radius of the Circle
        arc_center = [
            GisUtil.format_decimal_degree(circle_elem.xpath('geoLatCen/text()')[0]),
            GisUtil.format_decimal_degree(circle_elem.xpath('geoLongCen/text()')[0]),
            circle_elem.xpath('valCrc/text()')[0]]

        # Collect the radius
        arc_radius = GisUtil.format_geo_size(
            value=circle_elem.xpath('valRadius/text()')[0],
            unit=circle_elem.xpath('uomRadius/text()')[0])

        self._prepare_arc_lookup((arc_center[0], arc_center[1]), arc_radius)
        return self._arc_lookup

    # TODO: that looks like a Factory pattern : https://www.tutorialspoint.com/design_pattern/factory_pattern.htm
    # TODO : see GisDataFactory class for implementation idea
    def _airspace_free_geometry(self, ase_uid):
        """Create a polygon for a Free geometry

        Free geometry are made of points, border points, arc of circle

        Args:
            ase_uid ([string]): The UUID ot the Airspace

        Returns:
            [list]: a list of coordinates that can be used to create a "Polygon"
        """

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
                    GisUtil.format_decimal_degree(avx_elem.xpath('geoLat/text()')[0]),
                    GisUtil.format_decimal_degree(avx_elem.xpath('geoLong/text()')[0]),
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
                    GisUtil.format_decimal_degree(avx_elem.xpath('geoLatArc/text()')[0]),
                    GisUtil.format_decimal_degree(avx_elem.xpath('geoLongArc/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ]

                arc_radius = GisUtil.format_geo_size(
                    value=avx_elem.xpath('valRadiusArc/text()')[0],
                    unit=avx_elem.xpath('uomRadiusArc/text()')[0]
                )
            #TODO: Refactor to make it DRY (too similar with previous code extract)
            if avx_elem.xpath('codeType/text()')[0] == 'CWA':
                avx_function_buffer[1] = 'CWA'

                # Collect the center & the radius of the Circle Arc
                arc_center = [
                    GisUtil.format_decimal_degree(avx_elem.xpath('geoLatArc/text()')[0]),
                    GisUtil.format_decimal_degree(avx_elem.xpath('geoLongArc/text()')[0]),
                    avx_elem.xpath('valCrc/text()')[0]
                ]

                arc_radius = GisUtil.format_geo_size(
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
        """Extract a subset of Circle points forming a specific Arc of Circle

        TODO: confirm the arc_radius needs to be in meter

        Args:
            direction ([-1, 1]): Counter clockwise (-1) or clockwise (1) direction to move on circle
            arc_center ([lat, long]): The geo coord. (lat/long) of the Arc center
            arc_radius ([float]): The radius of the Arc
            arc_start ([lat, long]): The geo coord. (lat/long) of the start point of the Arc
            arc_stop ([lat, long]): The geo coord. (lat/long) of the end point of the Arc

        Returns:
            [list]: a list of coordinates that can be used to create a "Polygon"
        """

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
        """Circle points indexed "lookup" structure

        Args:
            arc_center ([lat, long]): the The geo coord. (lat/long) of the Circle center
            arc_radius ([float]): the radius of the Circle
        """

        # Cleanup to remove any previous circle "lookup" data from a previous circle
        logger.debug('Cleaning up the arc lookup structure')
        self._arc_lookup = []
        # Reprojected Circle (v3 because I tried several approach to get a proper circle drawn on a sphere)
        points = self._create_circle((arc_center[0], arc_center[1]), arc_radius)

        for i, point in enumerate(points):
            print(point)
            self._arc_lookup.append([point[1],point[0], i])

    def _get_idx_around_arc_point(self, latitude, longitude):
        """Define the index of the 2 circle points that are the closest from a POI (lat, long).

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
        """


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
        """Get the subset of the Arc point in the good direction

        Args:
            direction (-1, 1): counter-clockwise=-1, clockwise=1 
            index_start ([tupple]): the index of the 2 points around our first border point
            index_stop ([type]): the index of the 2 points around our last border point
        """

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
        """Get the subset of the relevant border point betwwen a start/stop border points
        
        Similar to the circle case, the border POI are close from the border but will
        most likely not exist as a border points in the AIXM source

        Args:
            gbr_uid ([string]): The uuid of the relevant border information discovered in the source
            border_start ([lat, long]): the first known point on the border 
            border_stop ([lat, long]): the last known point on the border
        
        Returns:
            [list]: a list of coordinates that can be used to create an important line of the Airspace polygon (i.e the border)
        """

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
        """Border points indexed "lookup" structure

        Args:
            gbr_uid ([string]): the UUID of the specific border segment in the source
        """

        # The <Gbr>
        gbr_elem = self.tree.xpath('//Gbr[GbrUid[@mid="' + gbr_uid + '"]]')

        # Find all <Gbv>
        gbv_elems = gbr_elem[0].xpath('Gbv')

        for gbv_elem in gbv_elems:
            # We need to be sure the points are coded in decimal degree
            # If not, we transform them
            geo_lat = GisUtil.format_decimal_degree(gbv_elem.xpath('geoLat/text()')[0])
            geo_long = GisUtil.format_decimal_degree(gbv_elem.xpath('geoLong/text()')[0])
            val_crc = gbv_elem.xpath('valCrc/text()')[0]
            self._border_lookup.append([geo_lat, geo_long, val_crc])

    def _get_crc_around_border_point(self, latitude, longitude):
        """Define the CRC of the 2 border points that are the closest from a POI (lat, long).

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
        """

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
        """Lookup the index of the border points based on the CRC value of the points
        
        TODO: There is probably a more pythonic way to perform this lookup in a list

        Args:
            val_crc ([tupple]): the 2 CRCs of consecutive border points
        
        Returns:
            [tuple]: the index value of the border points in our lookup structure 
        """

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
        """Extract the subset of the border points in the good direction

        Args:
            index_start ([tupple]): the index of the 2 points around our first border point
            index_stop ([tupple]): the index of the 2 points around our last border point
        """

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
        """Create a circle on Earth 

        Circle drawn in normal Cartesian geometry by shapely becomes Ellipsoid on Earth

        It is necessary to introduce a concept of projection   
        
        Args:
            center_point ([type]): [description]
            radius ([type]): [description]
        """


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

