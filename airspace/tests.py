'''Testing the briefing module
'''
from __future__ import absolute_import, division, print_function

import aixm_parser
import unittest
import datetime
import logging
logger = logging.getLogger(__name__)

class TestAixmParser(unittest.TestCase):

    def test_format_decimal_degree(self):

        self.assertEqual(
            float(-50.1234),
            aixm_parser.format_decimal_degree('050.1234W')
        )
        self.assertEqual(
            float(50.12345),
            aixm_parser.format_decimal_degree('050.12345E')
        )
        self.assertEqual(
            float(50.1234),
            aixm_parser.format_decimal_degree('50.1234N')
        )
        self.assertEqual(
            float(-50.12345),
            aixm_parser.format_decimal_degree('50.12345S')
        )

        self.assertEqual(
            float(-50.12345),
            aixm_parser.format_decimal_degree('50.12345S')
        )

        self.assertEqual(
            float('50.172286111111106'),
            aixm_parser.format_decimal_degree('501020.23N')
        )

        self.assertEqual(
            float('-50.172286111111106'),
            aixm_parser.format_decimal_degree('501020.23S')
        )

        self.assertEqual(
            float('-120.17249722222223'),
            aixm_parser.format_decimal_degree('1201020.99W')
        )

        self.assertEqual(
            float('120.17249722222223'),
            aixm_parser.format_decimal_degree('1201020.99E')
        )

        self.assertEqual(
            float('90.17222222222223'),
            aixm_parser.format_decimal_degree('0901020E')
        )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()

