from unittest import TestCase

from airspace.sources import AixmSource


class TestAixmSource(TestCase):
    def test_parse_xml(self):
        source = AixmSource("./airspace/tests/aixm_4.5_extract.xml")
        print(source.list_air_spaces())
