'''Testing the module
'''

from __future__ import absolute_import, division, print_function

import unittest
import datetime
import logging

from .sched_parser import ScheduleParser

logger = logging.getLogger(__name__)

class TestScheduleParser(unittest.TestCase):
    '''Basic Testing of the ScheduleParser

    Args:
        unittest ([type]): [description]
    '''


    def test_parsing(self):
        '''Testing multiple schedules
        '''


        tests_data = []
        tests_data.append(
            dict(
                schedule='MAR 31-APR 02 0730-1000 1130-1500 AND 03 0730-1000',
                effective_start=datetime.datetime(2018, 3, 10),
                effective_end=datetime.datetime(2018, 4, 20),
                expected_output=
                [
                    (datetime.datetime(2018, 3, 31, 7, 30), datetime.datetime(2018, 3, 31, 10, 0)),
                    (datetime.datetime(2018, 3, 31, 11, 30), datetime.datetime(2018, 3, 31, 15, 0)),
                    (datetime.datetime(2018, 4, 1, 7, 30), datetime.datetime(2018, 4, 1, 10, 0)),
                    (datetime.datetime(2018, 4, 1, 11, 30), datetime.datetime(2018, 4, 1, 15, 0)),
                    (datetime.datetime(2018, 4, 2, 7, 30), datetime.datetime(2018, 4, 2, 10, 0)),
                    (datetime.datetime(2018, 4, 2, 11, 30), datetime.datetime(2018, 4, 2, 15, 0)),
                    (datetime.datetime(2018, 4, 3, 7, 30), datetime.datetime(2018, 4, 3, 10, 0))
                ]
            )
        )

        tests_data.append(
            dict(
                schedule='MAR 31-APR 02 0730-1000 1130-1500 AND 03 0730-1000',
                effective_start=datetime.datetime(2018, 3, 10),
                effective_end=datetime.datetime(2018, 4, 20),
                expected_output=
                [
                    (datetime.datetime(2018, 3, 31, 7, 30), datetime.datetime(2018, 3, 31, 10, 0)),
                    (datetime.datetime(2018, 3, 31, 11, 30), datetime.datetime(2018, 3, 31, 15, 0)),
                    (datetime.datetime(2018, 4, 1, 7, 30), datetime.datetime(2018, 4, 1, 10, 0)),
                    (datetime.datetime(2018, 4, 1, 11, 30), datetime.datetime(2018, 4, 1, 15, 0)),
                    (datetime.datetime(2018, 4, 2, 7, 30), datetime.datetime(2018, 4, 2, 10, 0)),
                    (datetime.datetime(2018, 4, 2, 11, 30), datetime.datetime(2018, 4, 2, 15, 0)),
                    (datetime.datetime(2018, 4, 3, 7, 30), datetime.datetime(2018, 4, 3, 10, 0))
                ]
            )
        )

        tests_data.append(
            dict(
                schedule='DAILY 0700-1500 EXC SAT SUN',
                effective_start=datetime.datetime(2018, 3, 10),
                effective_end=datetime.datetime(2018, 3, 25),
                expected_output=
                [
                    (datetime.datetime(2018, 3, 12, 7, 0), datetime.datetime(2018, 3, 12, 15, 0)),
                    (datetime.datetime(2018, 3, 13, 7, 0), datetime.datetime(2018, 3, 13, 15, 0)),
                    (datetime.datetime(2018, 3, 14, 7, 0), datetime.datetime(2018, 3, 14, 15, 0)),
                    (datetime.datetime(2018, 3, 15, 7, 0), datetime.datetime(2018, 3, 15, 15, 0)),
                    (datetime.datetime(2018, 3, 16, 7, 0), datetime.datetime(2018, 3, 16, 15, 0)),
                    (datetime.datetime(2018, 3, 19, 7, 0), datetime.datetime(2018, 3, 19, 15, 0)),
                    (datetime.datetime(2018, 3, 20, 7, 0), datetime.datetime(2018, 3, 20, 15, 0)),
                    (datetime.datetime(2018, 3, 21, 7, 0), datetime.datetime(2018, 3, 21, 15, 0)),
                    (datetime.datetime(2018, 3, 22, 7, 0), datetime.datetime(2018, 3, 22, 15, 0)),
                    (datetime.datetime(2018, 3, 23, 7, 0), datetime.datetime(2018, 3, 23, 15, 0))
                ]
            )
        )

        test = ScheduleParser()
        for test_data in tests_data:
            test.parse(
                notam_begin=test_data['effective_start'],
                notam_end=test_data['effective_end'],
                data=test_data['schedule']
            )

            self.assertEqual(test.get_schedule(), test_data['expected_output'])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
