import lxml

from airspace.geometry import Border, GisDataFactory


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
        self.__borders = {}
        self.__air_spaces = {}
        self.parse_xml()

    def parse_xml(self):
        for border in self.__root.findall('Gbr'):
            border_object = Border
            uid = border.find('GbrUid')
            border_object.uuid = uid.get('mid')
            border_object.text_name = uid.find('txtName')
            border_object.code_type = border.find('codeType').text
            for point in border.findall('Gbv'):
                point_object = GisDataFactory.build_border_point(point.find('geoLat').text, point.find('geoLon').text,
                                                                 point.find('codeType').text, point.find('valCrc').text)
                border_object.append_border_point(point_object)
            self.add_border(border_object)

    def get_air_spaces(self):
        return self.__air_spaces

    def get_borders(self):
        return self.__borders

    def get_air_space(self, mid_uuid):
        return self.__air_spaces[mid_uuid]

    def get_border(self, mid_uuid):
        return self.__borders[mid_uuid]

    def add_border(self, border_object):
        self.__borders[border_object.getUuid()] = border_object

    def add_air_space(self, air_space_object):
        self.__air_spaces[air_space_object.getUuid()] = air_space_object
