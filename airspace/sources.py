import lxml


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

    def __init__(self, filename):
        """Initialize the AIXM source

        Args:
            filename ([type]): the file system file containing the AIXM 4.5 Airspace Informations
        """

        self.__filename = filename
        self.__tree = lxml.etree.parse(self.__filename)
        self.__borders = {}
        self.__air_spaces = {}

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
