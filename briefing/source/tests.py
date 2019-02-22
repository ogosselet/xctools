'''Testing the briefing module
'''
from __future__ import absolute_import, division, print_function

import unittest
import datetime
import logging

from .nats import NATS

logger = logging.getLogger(__name__)

class TestSource(unittest.TestCase):

    def test_natsparsing(self):

        source = NATS()
        file_briefing = open("./briefing/source/tests/nats.html", "r")
        # LXML doesn't like unicode strings (fix for Python3)
        #source.raw_area_briefing = file_briefing.read()
        source.raw_area_briefing = file_briefing.read().encode('utf-8')
        file_briefing.close()

        source._parse_area_briefing()

        # A few representative checks
        self.assertEqual(len(source.parsed_briefing), 334)
        self.assertEqual(source.parsed_briefing[150]['lower'], '4500FT AMSL')

        # Validate all entries got all the keys
        notam_keys = set(['a', 'b', 'c', 'upper', 'lower', 'e', 'src', 'q', 'sched', 'ref'])
        for notam in source.parsed_briefing:
            self.assertTrue(notam_keys.issubset(notam))

        #TODO: We will add more assert to cover issues we will detect in production and that
        # we will fix in next releases.

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
