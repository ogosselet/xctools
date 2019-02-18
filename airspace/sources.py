import lxml

from airspace.geometry import Border, Airspace
from airspace.util import GisPointFactory


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
        self.__tree = lxml.etree.parse(self.__filename)
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
                point_object = GisPointFactory.build_border_point(point.find('geoLat').text, point.find('geoLon').text,
                                                                  point.find('codeType').text,
                                                                  point.find('valCrc').text)
                border_object.append_border_point(point_object)
            self.add_border(border_object)

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
