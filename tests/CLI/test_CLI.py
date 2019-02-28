from unittest import TestCase

from airspace.sources import AixmSource


class TestCLI(TestCase):
    source = None

    def __init__(self, *args, **kwargs):
        super(TestCLI, self).__init__(*args, **kwargs)
        self.source = AixmSource('airspace/tests/aixm_4.5_extract.xml')

    def test_list_borders(self):
        challenge = 'BELGIUM_FRANCE\t19048558\n'
        payload = ""
        for border in self.source.get_borders():
            payload += border.text_name + '\t' + str(border.uuid) + '\n'
        self.assertEqual(payload, challenge)

    def test_list_airspaces(self):
        challenge = 'ARDENNES 05\t100760256\t19048558\nLESSIVE\t400001601922575\tno border crossed\n'
        payload = ""
        for air_space in self.source.get_air_spaces():
            if len(air_space.border_crossings) > 0:
                crossing_list = ""
                for crossing in air_space.border_crossings:
                    if crossing_list == "":
                        crossing_list += str(crossing.related_border_uuid)
                    else:
                        crossing_list += ", " + str(crossing.related_border_uuid)
            else:
                crossing_list = "no border crossed"
            payload += air_space.text_name + '\t' + str(air_space.uuid) + '\t' + crossing_list + '\n'
        self.assertEqual(payload, challenge)
