from unittest import TestCase

from airspace.sources import FloatGisPoint, GisUtil, DmsGisPoint


class TestGisUtil(TestCase):

    def test_dd2dms(self):
        aixm_dms_formatted_str = "510521.37N"
        dd = GisUtil.format_decimal_degree(aixm_dms_formatted_str)
        self.assertEqual(GisUtil.dd2dms(dd, False), aixm_dms_formatted_str)

    def test_float_gis_points(self):
        a = FloatGisPoint(50.1234567890123, 4.1234567890123, "123456", "test")
        b = FloatGisPoint(50.1234567890023, 4.1234567890023, "1234568", "test")
        self.assertEqual(a, b)

    def test_dd_and_dms_equality(self):

        dms_point = DmsGisPoint('502536N', '0050543E', "456", "test")

        float_point = FloatGisPoint(50.426667, 5.095278, "966", 'test')

        self.assertEqual(dms_point, float_point)

    def test_format_decimal_degree(self):
        self.assertEqual(
            float(-50.1234),
            GisUtil.format_decimal_degree('050.1234W')
        )
        self.assertEqual(
            float(50.12345),
            GisUtil.format_decimal_degree('050.12345E')
        )
        self.assertEqual(
            float(50.1234),
            GisUtil.format_decimal_degree('50.1234N')
        )
        self.assertEqual(
            float(-50.12345),
            GisUtil.format_decimal_degree('50.12345S')
        )

        self.assertEqual(
            float(-50.12345),
            GisUtil.format_decimal_degree('50.12345S')
        )

        self.assertEqual(
            float('50.172286111111106'),
            GisUtil.format_decimal_degree('501020.23N')
        )

        self.assertEqual(
            float('-50.172286111111106'),
            GisUtil.format_decimal_degree('501020.23S')
        )

        self.assertEqual(
            float('-120.17249722222223'),
            GisUtil.format_decimal_degree('1201020.99W')
        )

        self.assertEqual(
            float('120.17249722222223'),
            GisUtil.format_decimal_degree('1201020.99E')
        )

        self.assertEqual(
            float('90.17222222222223'),
            GisUtil.format_decimal_degree('0901020E')
        )
