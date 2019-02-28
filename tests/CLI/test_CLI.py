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
