from unittest import TestCase

from airspace.sources import FloatGisPoint, GisUtil


class TestGisUtil(TestCase):

    def test_dd2dms(self):
        aixm_dms_formatted_str = "510521.37N"
        dd = GisUtil.format_decimal_degree(aixm_dms_formatted_str)
        self.assertEqual(GisUtil.dd2dms(dd, False), aixm_dms_formatted_str)

    def test_float_gis_points(self):
        a = FloatGisPoint(50.1234567890123, 4.1234567890123)
        b = FloatGisPoint(50.1234567890023, 4.1234567890023)
        self.assertEqual(a, b)
