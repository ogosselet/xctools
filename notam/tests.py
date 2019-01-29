'''Testing the module
'''

from __future__ import absolute_import, division, print_function

import unittest
import datetime
import logging
import ast

from .sched_parser import ScheduleParser
from .notam import Notam

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

class TestNotam(unittest.TestCase):

    def test_notam(self):

        notam_str = "{'a': 'LFPM', 'upper': '4500FT AMSL', 'c': '18/10/26 16:00', 'b': '18/03/26 07:00', 'e': 'TEMPORARY RESTRICTED AREA (ZRT) MELUN VILLAROCHE AERODROME DUE TO AEROBATICS : - AEROBATICS CHARACTERISTICS (ACTIVITY DURING LFPM ATS HOURS) :   . PSN : 483649N 0024025E   . AXIS : 103/283 CENTRED ON PSN   . LENGTH : 7200M   . VERTICAL LIMITS : 500FT AGL/4500FT AMSL WHEN ZRT ACTIVATED                       500FT AGL/2500FT AMSL WHEN ZRT NOT ACT   . ACTIVITY RESERVED TO ACFT AUTHORIZED ACCORDING TO THE PROTOCOL. - ZRT CHARACTERISTICS (ONLY DURING LFPM ATS HOURS) :   . LATERAL LIMITS :     483753N 0023748E     483701N 0024330E     483545N 0024304E     483637N 0023721E     483753N 0023748E   . VERTICAL LIMITS :     2500FT AMSL/4500FT AMSL   . STATUS :     TEMPO RESTRICTED AREA (ZRT) WHEN ACTIVATED REPLACES THE      OVERLAPPING PARTS OF AIRSPACE.   . SERVICES PROVIDED :     INFORMATION FLIGHT AND ALERT BY MELUN TWR.   . ENTRY CONDITIONS GAT/OAT :     COMPULSORY AREA AVOIDANCE DURING ACTIVITY EXC :      ACFT INVOLVED IN AEROBATICS     ACFT CARRYING OUT ASSISTANCE, RESCUE OR PUBLIC SAFETY  OPERATIONS WHEN THEIR MISSIONS ARE NOT COMPATIBLE WITH THE AREA     AVOIDANCE AND AFTER PRIOR RADIO CONTACT TO MELUN TWR. - INFORMATION FOR AIR USERS :   ACTUAL ACTIVITY AVBL FROM MELUN TWR  121.100MHZ                             MELUN ATIS 128.175MHZ                             SEINE INFO 134.300MHZ                             ORLY APP   123.875MHZ', 'src': 'NATS', 'lower': '500FT AGL', 'q': 'LFFF/QRTCA/IV/BO/AW/005/045/4837N00240E003', 'sched': 'MON-FRI 0700-1600 EXC APR 02 MAY 01 08 10 21 AUG 15', 'ref': 'R0576/18'}"

        notam = Notam(ast.literal_eval(notam_str))

        # Let's assert a few fields around
        self.assertEqual(notam.icao, 'LFFF')
        self.assertEqual(notam.fl_lower, '005')
        self.assertEqual(notam.reference, 'R0576/18')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
