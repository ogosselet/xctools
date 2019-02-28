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

    def test_extract_borders(self):
        ais = self.source.get_air_space(args.extract_borders)
        if ais is not None:
            if len(ais.border_crossings) > 0:
                cpt = 1
                for crossing in ais.border_crossings:
                    print('# border crossing ' + str(
                        cpt) + ' : ' + crossing.related_border_name + '(' + crossing.related_border_uuid + ')')
                    print('')
                    pts_txt = ""
                    for pt in crossing.common_points:
                        pts_txt += "DP " + pt.get_oa_lat() + " " + pt.get_oa_lon() + " "
                    print(pts_txt)
                    cpt += 1
            else:
                print('airspace uuid : ' + args.extract_borders + " does not cross any border.")
        else:
            print('was not able to find airspace uuid : ' + args.extract_borders)
