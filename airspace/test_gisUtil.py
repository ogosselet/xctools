from unittest import TestCase

from airspace.geometry import GisUtil


class TestGisUtil(TestCase):

    def test_dd2dms(self):
        aixm_dms_formatted_str = "510521.37N"
        dd = GisUtil.format_decimal_degree(aixm_dms_formatted_str)
        self.assertEqual(GisUtil.dd2dms(dd, False), aixm_dms_formatted_str)
