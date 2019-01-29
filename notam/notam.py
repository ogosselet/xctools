'''NOTAM notam.notam Module'''

from __future__ import absolute_import, division, print_function

import logging
import re
import datetime

logger = logging.getLogger(__name__)

class NotamError(Exception):
    '''Exception class building a common message format including NOTAM info

    Args:
        Exception (object): Exception as superclass

    '''

    def __init__(self, notam, msg=None):
        '''Init the superclass "Exception" string

        Args:
            notam ([Notam]): the Notam object where the exception was triggered
            msg ([str], optional): Defaults to None. The contextual message of the Exception
        '''

        if msg is None:
            # Set some default useful error message
            msg = 'unexpected error'
        exc_msg = 'NOTAM {}: {}'.format(notam.reference, msg)

        super(NotamError, self).__init__(exc_msg)
        self.notam = notam


class DecodingError(NotamError):
    '''Exception raised when a NOTAM decoding error is detected

    Decoding means building a Notam object based on strings with the expected format
    and content as provided by the Notam source

    Args:
        NotamError (Exception): NotamError as superclass
    '''

    def __init__(self, notam, msg=None):
        '''Init the superclass NotamError message

        Args:
            notam ([Notam]): the Notam object where the exception was triggered
            msg ([str], optional): Defaults to None (replaced by a generic message).
                The contextual message of the Exception
        '''

        if msg is None:
            msg = 'unexpected decoding error'
        super(DecodingError, self).__init__(notam, msg)


class Notam(object):
    '''Main Notam class (purpose of the module)

    A NOTAM object is constructed from the string representation of all NOTAM fields
    a), b), c), e), q), Lower, Upper, Schedule, ... with the goal to enhance the
    programatic value of the NOTAM data present in the briefing.

    The relevant python types & data structure are used as much as possible for example:

        - date/datetime
        - Schedule information data ('b', 'c' & 'sched') are expanded as a list of timeslots (i.e. Start/Stop Datetime)
        - some 'q' line codes are extracted (admin info, geo-localisation, ...)

    More info on the qline decoded by the following regex will be provided as class attributes
    documentation.

    :regex: 
        r'(?P<icao>[A-Z]{4})
        /Q(?P<subject>[A-Z]{2})(?P<status>[A-Z]{2}
        /(?P<traffic>[I,V]{1,2})
        /(?P<relevance>[N,B,O,M,K]{1,3})
        /(?P<scope>A{0,1}E{0,1}W{0,1}
        /(?P<fl_lower>[0-9]{3}
        /(?P<fl_upper>[0-9]{3}
        /(?P<coord_radius>.*)

    Attributes:
        <icoa> (str): ICAO location indicator in which the facility, airspace or condition
            reported on is located (Ex: EBBU, LFFF, ...)

        <subject> (str): Identify the Subject
        
                - RR: Restricted Area
                - RD: Danger Area
                - OB: Obstacle
                - ...

            => The full <subject> requires 2 letters to be fully qualified but
            the first letter gives already information on a group of subject.

                - R: Nav. Warnings Airspace Resrictions
                - W: Nav. Warnings
                - ...


            We might decide to maintain the full list of code to help in the
            NOTAM decode exercise in a separate file (easy to maintain in a versioning system)

        <status> (str): Define the Status or the Condition of the Subject
            
                - CA: Changes "Activated",
                - CD: Changes "Deactivated",
                - CR: Temporarily "Replaced by,
                - CN: Canceled
                - ...

            => The full <status> requires 2 letters to be fully qualified but
            the first letter gives already information on the category of subjects.

                - A: Availability
                - C: Changes
                - H: Hazard

        <traffic> (str): Define the "type" traffic affected by the NOTAM (up to 2 letters from the list below)

                - I: IFR
                - V: VFR

            As paraglider pilot we are concerned by NOTAM containing a "V" as we flight under
            the "VFR" rules

        <relevance> (str): Define the "relevance" of the NOTAM (up to 3 letters from the list below)

                - N: NOTAM of Immediate attention for flight crew members
                - B: NOTAM selected for PIB entry
                - M: Misceallenous NOTAM
                - K: Checklist NOTAM
                - O: FLight Operations NOTAM

            We often see the NBO, BO & M combinations

        <scope> (str): Define the "scope" of the NOTAM (up to 2 letters from the list below - note our "simplified" regex)

                - A: Aerodrome
                - E: En-route
                - W: Nav Warning
                - K: Notam in checklist (used ?)

        <fl_lower>, <fl_upper>: Lower & Upper Limit expressed in Flight Level and rounded down or up to the nearest 100 ft increment

        <coord_radius>: Four digits followed by N or S followed by five digits followed by E or W and three digits radius.

            This qualifier allows the geographical association of a NOTAM to a facility, service or area that corresponds to the aerodrome or FIR(s)
            We will further decode this as a real "GEO" information

        <sched>: a semantic string representation of a notam schedule. 
            
            Supported format are visible in the sched_parser module

    Args:
        object ([object]): superclass

    Raises:
        DecodingError: exception raised when something wrong happen during the decoding phase of the NOTAM

    '''

    def __init__(self, notam_string_dict):
        self.reference = notam_string_dict['ref']
        self.start_time = self._strdatetime_to_datetime(notam_string_dict['b'])
        self.end_time = self._strdatetime_to_datetime(notam_string_dict['c'])
        self.lower = notam_string_dict['lower']
        self.upper = notam_string_dict['upper']
        self.full_q_line = notam_string_dict['q']
        self.sched = notam_string_dict.get('sched', '')
        self.source = notam_string_dict.get('src')
        self.text = notam_string_dict.get('e')
        # Explode the Q Line
        self._parse_q_line()

    def _parse_q_line(self):
        q_match = re.search(
            r'(?P<icao>[A-Z]{4})/Q(?P<subject>[A-Z]{2})'
            r'(?P<status>[A-Z]{2})/(?P<traffic>[I,V]{1,2})/(?P<relevance>[N,B,O,M,K]{1,3})'
            r'/(?P<scope>A{0,1}E{0,1}W{0,1})/(?P<fl_lower>[0-9]{3})/(?P<fl_upper>[0-9]{3})'
            r'/(?P<coord_radius>.*)',
            self.full_q_line
            )
        if q_match:
            self.icao = q_match.group('icao')
            self.subject = q_match.group('subject')
            self.status = q_match.group('status')
            self.traffic = q_match.group('traffic')
            self.relevance = q_match.group('relevance')
            self.scope = q_match.group('scope')
            self.fl_lower = q_match.group('fl_lower')
            self.fl_upper = q_match.group('fl_upper')
            self.coord_radius = q_match.group('coord_radius')
        else:
            raise DecodingError(self, 'Unsupported q_line format "{}"'.format(self.full_q_line))

    def _strdatetime_to_datetime(self, strdatetime):
        ''' Converts a NOTAM datetime string into a python datetime

            Raise an Exception if conversion is not successfull

            Args:
                str: Datetime as a NOTAM string
            Returns:
                datetime
        '''

        # 16/03/01 05:00
        datetime_match = re.search(
            r'(?P<year>[0-9]{2})'
            r'/(?P<month>[0-9]{2})/(?P<day>[0-9]{2}) (?P<hour>[0-9]{2})\:(?P<min>[0-9]{2})',
            strdatetime
            )
        if datetime_match:
            try:
                # So far so good for a datetime ...
                year = int(datetime_match.group('year'))
                month = int(datetime_match.group('month'))
                day = int(datetime_match.group('day'))
                hour = int(datetime_match.group('hour'))
                minute = int(datetime_match.group('min'))
                return datetime.datetime(2000 + int(year), month, day, hour, minute)
            except Exception:
                logger.error(
                    '%s - Cannot convert "%s" into a datetime', self.reference, strdatetime
                    )

        # The only other thing we support is a PERM
        if re.search(r'(?P<perm>PERM)', strdatetime):
            # There should be another system to manage NOTAM by 2099
            return datetime.datetime(2099, 12, 31, 23, 59)

        # If we reach this point, we need to raise an exception and implement the
        # missing date format
        raise DecodingError(self, 'Unsupported date string {}'.format(str))
