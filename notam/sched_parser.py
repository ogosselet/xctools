'''NOTAM Schedule Parser

Raises:
    LexerWarning: Exception raised when a Lexer tokenization error is detected
'''

from __future__ import absolute_import, division, print_function

import datetime
import calendar
import logging

import ply.lex as lex
import ply.yacc as yacc

# Schedule format supported:
#
# Historical:-)
# JAN 26-30 0730-1500

# JAN 12 0900-1600, 13 0700-1800, 14-18 0700-1600, 19-20 0700-2200, 21 0700-1600,
# 22 0700-1500, 26 0800-2200, 27 0700-1600, 28 0700-2200 AND 29-31 0700-1600

# DAILY SR-SS

# JAN 27 0900-0950 1800-1850, 28 1000-1050, 29 AND 30 1400-1450

# DAILY 0700-1500 EXC SAT SUN

# DAILY 0530-2100

# FEB 17 AND 18 0900-1100 1230-1600

# JAN 12 0900-1600, 13 0700-1800, 14-18 0700-1600, 19-20 0700-2200, 21 0700-1600,
# 22 0700-1500, 26 0800-2200, 27 0700-1600, 28 0700-2200 AND 29-31 0700-1600

# JAN 19 20 AND 27 SS-2100

# FEB 03 10 19 24 0930-1100, 04 1130-1300 AND 05 11 0730-1300

# MAY 14 08:00 Till:PERM

# JAN 15 09:34 Till:13 MAY 15 08:00 EST

# MON-FRI 0630-1600
#
# Newer:
# MON-FRI H24 more precisely the H24 interpreted as 0000-2359 (* added on the 24/01/17 *)

# To be checked: (this might already be fixed)
# Two type of schedule made the parser failed. This is happening when close from the end of a month.
# MAR 31 AND APR 01-03 0630-1400
# MAR 31-APR 02 0730-1000 1130-1500 AND 03 0730-1000 (this was fixed)

# Get an instance of a logger
logger = logging.getLogger(__name__)

MONTH = {'JAN':1,
         'FEB':2,
         'MAR':3,
         'APR':4,
         'MAY':5,
         'JUN':6,
         'JUL':7,
         'AUG':8,
         'SEP':9,
         'OCT':10,
         'NOV':11,
         'DEC':12}

WEEK = {'MON':0,
        'TUE':1,
        'WED':2,
        'THU':3,
        'FRI':4,
        'SAT':5,
        'SUN':6,
        'HOL':7}

class PlyError(Exception):
    '''Exception class building a common message format for schedule parser

    Args:
        Exception (object): Exception as superclass

    '''

    def __init__(self, sched_string, msg=None):
        '''Init the superclass "Exception" string

        Args:
            notam ([Notam]): the Notam object where the exception was triggered
            msg ([str], optional): Defaults to None. The contextual message of the Exception
        '''

        if msg is None:
            # Set some default useful error message
            msg = 'unexpected error'
        exc_msg = 'Schedule string {}: {}'.format(sched_string, msg)

        super(PlyError, self).__init__(exc_msg)

class LexerWarning(PlyError):
    '''Exception raised when a Lexer tokenization error is detected

    Args:
        PlyError (Exception): PlyError as superclass
    '''

    def __init__(self, lexer, token_char):
        '''Init the superclass PlyError message

        Args:
            notam ([Notam]): the Notam object where the exception was triggered
            msg ([str], optional): Defaults to None (replaced by a generic message).
                The contextual message of the Exception
        '''

        exc_msg = 'Unexpected character "{}" skipped at pos {}'.format(token_char, lexer.lexpos)
        super(LexerWarning, self).__init__(lexer.lexdata, exc_msg)


class ScheduleLexer():
    '''PLY Lexer for the Schedule field of the NOTAM

    Break the schedule text into a collection of tokens specified by a set of regular expression rules.
    '''

    # List of token names. This is always required
    tokens = (
        'MONTH',
        'DATE',
        'HOUR',
        'DAY',
        'H24',
        'DAILY',
        'EVERY',
        'HOL', # Holidays
        'EXC', # Exclude
        'SUNRISE',
        'SUNSET',
        'RANGE',
        'PLUS',
        'MINUS',
        'AND',
        'GROUP',
    )

    # Regular expression rules for simple tokens
    t_MONTH = r'JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC'
    t_DATE = r'[0-3][0-9]'
    t_HOUR = r'[0-2][0-9][0-5][0-9]'
    t_DAY = r'MON|TUE|WED|THU|FRI|SAT|SUN'
    t_H24 = r'H24'
    t_HOL = r'HOL'
    t_DAILY = r'DAILY'
    t_EVERY = r'EVERY'
    t_SUNRISE = r'SR'
    t_SUNSET = r'SS'
    t_EXC = r'EXC'
    t_RANGE = r'-'
    t_PLUS = r'PLUS'
    t_MINUS = r'MINUS'
    t_AND = r'AND'
    t_GROUP = r',|\n'

    def t_newline(self, t):
        ''' Tracking number of newlines

        '''

        #r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Error handling rule
    def t_error(self, t):
        '''Executed when the lexer is discovering an undefined token character

        Args:
            t ([char]): the unexpected character
        '''

        # Option 1)
        # Raise and exception and stop the parsing
        raise LexerWarning(self.lexer, t.value[0])
        # Option 2)
        # Log something and skip the wrong character to continue the parsing
        # logger.debug("Illegal character %s",t.value[0])
        # t.lexer.skip(1)

    #def build(self, **kwargs):
    #    '''Building the lexer
    #    '''
    #
    #    logger.debug('Building lexer')
    #    self.lexer = lex.lex(module=self, **kwargs)
    #    logger.debug('Building lexer done')

    def __init__(self):
        '''Lexer constructor
        '''

        self.lexer = lex.lex(module=self)

    # Test it output
    def test(self, data):
        '''Perform a test execution of the lexer

        This method is usefull to check or debug if the tokens regexp matches the input text as expected

        Args:
            data ([string]): schedule input string
        '''

        logger.debug(data)
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            logger.debug(tok)


class ScheduleParser():
    '''PLY Parser for the schedule field of a NOTAM

    Each activation slots described by the syntax of the schedule text is expanded as a list of 
    datetime tuple (datetime_start, datetime_stop)
    '''

    tokens = ScheduleLexer.tokens


    #parsed_sched = []
    #sched_type = ''
    #month = ''

    #sched_multimonth = False
    #month_start = ''
    #date_start = ''
    #month_end = ''
    #date_end = ''

    #sched_differed = False
    #month_differed = ''
    #dates_differed = []
    #pending_differed = False
    #ps_differed = {}

    #dates = []

    #dates1 = []
    #dates2 = []
    #days = []
    #exc = []
    #timerange = []


    # A "Schedule" contains multiple "Timeslice"
    def p_schedule(self, p):
        """schedule : timeslice schedule
                    | timeslice
        """
        if len(p) == 3:
            # Parser reduction
            p[0] = p[2]
            logger.debug('schedule: more timeslice detected')
        else:
            logger.debug('schedule: Lexer/Parser reduction completed')



    # A "Timeslice" is made of one or more "Complex Date"
    # GROUP (',' or 'newline') and AND (AND) are reduced here
    def p_timeslice(self, p):
        """timeslice : complexdate GROUP
                     | complexdate AND
                     | complexdate
        """
        # We need to sum up this timeslice using the _store contents, the states,...
        # and "expand" our schedule

        # Common pre-processing
        ts_year = self._notam_begin.year

        if self._store_month:
            ts_month = self._store_month
            logger.debug('timeslice: using numeric month=%s reduced in this timeslice', ts_month)
        else:
            ts_month = self._ref_month
            logger.debug('timeslice: using last numeric reference month=%s', ts_month)

        # We have different cases:

        #start_month = self._notam_begin.month
        #last_month = None

        # Expanding timeslice
        # Day Mode: ex. MON-FRI 1000-1400
        if self._day_mode:
            logger.debug('timeslice: reduction operating in day mode')
            notam_span = self._notam_end - self._notam_begin
            # Removing all days that were excluded
            for day in self._store_exc_weekdays:
                try:
                    self._store_weekdays.remove(day)
                except:
                    logger.warning("Excluded day cannot be removed. It was not added first !")
            # Expand the timeslice for the complete Notam date "span"
            for i in range(notam_span.days + 1):
                ts_day = self._notam_begin + datetime.timedelta(i)
                # Checking if the weekday is in the list
                if ts_day.weekday() in self._store_weekdays:
                    # Adding all reduced timerange
                    for trange in self._store_timerange:
                        #logger.debug(delta)
                        ts_start = ts_day + trange[0]
                        ts_stop = ts_day + trange[1]
                        self._store_timeslice.append((ts_start, ts_stop))

            logger.debug('timeslice: reduced !')
            self._store_schedule.extend(self._store_timeslice)
            self._set_timeslice_initial_state(ref_month=ts_month)
        # Multi-month Mode: ex.
        elif self._multimonth:
            logger.debug('timeslice: reduction operating in multimonth mode')
            ts_span = self._store_multimonth[1] - self._store_multimonth[0]
            # Buidling the list of dates now ...
            for i in range(ts_span.days + 1):
                ts_day = self._store_multimonth[0] + datetime.timedelta(days=i)
                for trange in self._store_timerange:
                    ts_start = ts_day + trange[0]
                    ts_stop = ts_day + trange[1]
                    self._store_timeslice.append((ts_start, ts_stop))
            self._store_schedule.extend(self._store_timeslice)
            # Sliding the reference month
            self._set_timeslice_initial_state(ref_month=self._store_multimonth[1].month)
            # TODO: add reference year & related sliding if multimonth span 2 years ?
        else:
            logger.debug('timeslice: reduction operating in date mode')
            for ts_day in self._store_dates:
                for trange in self._store_timerange:
                    ts_start = datetime.datetime(ts_year, ts_month, ts_day) + trange[0]
                    ts_stop = datetime.datetime(ts_year, ts_month, ts_day) + trange[1]
                    self._store_timeslice.append((ts_start, ts_stop))
            self._store_schedule.extend(self._store_timeslice)
            self._set_timeslice_initial_state(ref_month=ts_month)

#        if self.sched_multimonth and not self.sched_datelist:
#            yy = datetime.date.today().year
#            for i in range(MONTH[self.month_start],1 + MONTH[self.month_end]):
#                if i == int(MONTH[self.month_start]):
#                    logger.debug('First month ' + self.month_start)
#                    last_month_day = calendar.monthrange(yy,MONTH[self.month_start])[1]
#                    logger.debug('First month last day ' + str(last_month_day))
#                    ps = {'sched_type': '1',
#                        'month': self.month_start,
#                        'dates': self.dates + range(int(self.date_start),1+last_month_day),
#                        'days': self.days,
#                        'timeranges': self.timeranges}
#                    self.parsed_sched.append(ps)
#                    logger.debug(ps)
#                if i == int(MONTH[self.month_end]):
#                    logger.debug('Last month ' + self.month_end)
#                    # Required because of SCHEDULE:
#                    #    MAR 31-APR 02 0730-1000 1130-1500 AND 03 0730-1000
#                    self.month = self.month_end
#                    ps = {'sched_type': '1',
#                        'month': self.month_end,
#                        'dates': self.dates + range(1,1+int(self.date_end)),
#                        'days': self.days,
#                        'timeranges': self.timeranges}
#                    self.parsed_sched.append(ps)
#                    logger.debug(ps)
#                if i > int(MONTH[self.month_start]) and i < int(MONTH[self.month_end]):
#                    logger.debug('In between month')
#                    last_month_day = calendar.monthrange(yy,i)[1]
#                    ps = {'sched_type': '1',
#                        'month': MONTH.keys()[MONTH.values().index(i)],
#                        'dates': self.dates + range(1,1 + last_month_day),
#                        'days': self.days,
#                        'timeranges': self.timeranges}
#                    self.parsed_sched.append(ps)
#                    logger.debug(ps)
#        elif self.sched_multimonth and self.sched_datelist:
#            print("Our new pattern !!!!")
#            ps = {'sched_type': '1',
#                  'month': self.month1,
#                  'dates': self.dates1,
#                  'days': self.days,
#                  'timeranges': self.timeranges}
#            self.parsed_sched.append(ps)
#            ps = {'sched_type': '1',
#                  'month': self.month2,
#                  'dates': self.dates2,
#                  'days': self.days,
#                  'timeranges': self.timeranges}
#            self.parsed_sched.append(ps)
#            #self.month_differed = self.month_end
#            logger.debug(ps)
#        elif self.sched_differed:
#            # We have a deferred date that will use the same timeslot
#            logger.debug('Storing info with pending timeslot ...')
#            self.ps_differed = {'sched_type': '1',
#                  'month': self.month_differed,
#                  'dates': self.dates_differed,
#                  'days': self.days,
#                  'timeranges' : ''
#            }
#            logger.debug(self.ps_differed)
#            self.sched_differed = False
#            self.pending_differed = True
#        else:
#            if self.pending_differed:
#                # We still have a pending differed to add
#                logger.debug('Pending timeslot is now available ...')
#                self.ps_differed['timeranges'] = self.timeranges
#                self.parsed_sched.append(self.ps_differed)
#                logger.debug(self.ps_differed)
#                self.pending_differed = False
#                self.ps_differed = {}
#
#            ps = {'sched_type': self.sched_type,
#                  'month': self.month,
#                  'dates': self.dates,
#                  'days': self.days,
#                  'timeranges': self.timeranges}
#            self.parsed_sched.append(ps)
#            logger.debug(ps)
#
#        self.sched_multimonth = False
#        self.sched_type = ''
#        # month = '' we skip the month, it stays valid unless "refreshed"
#        self.dates = []
#        self.days =  []
#        self.timeranges = []
#
    # There are many forms of "Complex Date"
    def p_complexdate_partial(self, p):
        """complexdate : MONTH DATE AND
        """
        logger.debug('complexdate_partial: the timeslot is not yet available')

        # We store what we should
        #self._store_month = MONTH[p[1]]
        self._store_month = MONTH[p[1]]
        self._store_dates.append(int(p[2]))

        # We flag that our schedule is not yet complete
        self._flag_sched_differed = True


    def p_complexdate_with_month(self, p):
        """complexdate : MONTH datelist timeslots
                       | MONTH daterange timeslots
        """
        logger.debug('complexdate_with_month: stored month=%s', p[1])
        #self.sched_type = '1'
        self._store_month = MONTH[p[1]]

        logger.debug('complexdate_with_month: updating ref_month=%s', p[1])
        self._ref_month = MONTH[p[1]]

    def p_complexdate(self, p):
        """complexdate : datelist timeslots
                       | daterange timeslots
        """
        # logger.debug('complexdate: detected (using month "%s" previously reduced)',
        # self._ref_month)
        logger.debug('complexdate: no month specified')
        #self.sched_type = '1'

    def p_complexdate_with_exc(self, p):
        """complexdate : datelist timeslots exclusion
        """
        logger.debug('complexdate_with_exc: detected')
        #self.sched_type = '2'

    def p_complexdate_with_month_and_exc(self, p):
        """complexdate : MONTH datelist timeslots exclusion
        """
        logger.debug('complexdate_with_month_and_exc: detected')
        #self.sched_type = '2'
        #self.month = p[1]
        logger.debug('complexdate_with_month_and_exc: reducing month %s', p[1])
        self._store_month = p[1]

    def p_complexdate_with_months(self, p):
        """complexdate : MONTH DATE RANGE MONTH DATE timeslots
        """

        start_year = self._notam_begin.year
        logger.debug('complexdate_with_months: switching to multimonth')
        self._multimonth = True
        begin_date = datetime.datetime(start_year, MONTH[p[1]], int(p[2]))
        end_date = datetime.datetime(start_year, MONTH[p[4]], int(p[5]))
        if end_date < begin_date:
            # Looks like we are spanning 2 years
            logger.debug('complexdate_with_months: spanning 2 years. Added 1Y to second date')
            end_date = end_date + datetime.timedelta(year=1)
        self._store_multimonth = (begin_date, end_date)


    # MAR 31 AND APR 01-03 0630-1400
    def p_complexdatelist_with_months(self, p):
        """complexdate : MONTH datelist1 MONTH datelist2 timeslots
        """
        logger.debug('NOTAM Date List spanning 2 months : ')
        self._multimonth = True
        self.sched_datelist = True
        self.month1 = p[1]
        #self.date_start = p[2]
        self.month2 = p[3]
        #self.date_end = p[5]
        logger.debug('NOTAM months 1: %s', self.month1)
        logger.debug('NOTAM months 2: %s', self.month2)
        self.month = p[3]


    def p_complexdate_daily(self, p):
        """complexdate : DAILY timeslots
        """
        logger.debug('complexdate_daily: switching to day mode')
        self._day_mode = True
        self._store_weekdays = [0, 1, 2, 3, 4, 5, 6, 7]

    def p_complexdate_timeslots(self, p):
        """complexdate : timeslots
        """
        logger.debug('complexdate_timeslots: detected')
        #self.sched_type = '4'

    def p_complexdate_daylist(self, p):
        """complexdate : daylist timeslots
        """
        logger.debug('complexdate_daylist: switching to day mode')
        self._day_mode = True
        #self.sched_type = '3'
        #self.days = [1,2,3,4,5,6,7,8]

    def p_complexdate_dayrange(self, p):
        """complexdate : dayrange timeslots
        """
        logger.debug('complexdate_dayrange: detected')
        #self.sched_type = '3'
        #self.days = [1,2,3,4,5,6,7,8]


    def p_complexdate_daily_with_exc(self, p):
        """complexdate : DAILY timeslots exclusion
        """
        logger.debug('complexdate_daily_with_exc: detected')
        self._day_mode = True
        self._store_weekdays = [0, 1, 2, 3, 4, 5, 6, 7]

    def p_complexdate_weekday_range(self, p):
        """dayrange : DAY RANGE DAY
        """
        logger.debug('complexdate_weekday_range: switching to day mode')
        self._day_mode = True
        # Is there anything in self._store_weekdays already ?
        self._store_weekdays = self._store_weekdays + range(int(WEEK[p[1]]), 1+int(WEEK[p[3]]))

    def p_datelist(self, p):
        """datelist : DATE datelist
                    | DATE AND DATE
                    | DATE
        """
        if len(p) == 3:
            p[0] = p[2]
            # Reduced Token needs to be added
            logger.debug('datelist: stored date=%s', p[1])
            self._store_dates.append(int(p[1]))
        if len(p) == 4:
            logger.debug('datelist: stored date=%s & date=%s', p[1], p[3])
            self._store_dates.append(int(p[1]))
            self._store_dates.append(int(p[3]))
        # Replacing
        # logger.debug('NOTAM Date : ' + p[1])
        # self.dates.append(int(p[1]))
        # By
        if len(p) == 2:
            logger.debug('datelist: stored date=%s', p[1])
            self._store_dates.append(int(p[1]))

    def p_datelist1(self, p):
        """datelist1 : DATE datelist1
                     | DATE AND DATE
                     | DATE
        """
        if len(p) == 3:
            p[0] = p[2]
            # Reduced Token needs to be added
            logger.debug('NOTAM Date : %s', p[1])
            self.dates1.append(int(p[1]))
        if len(p) == 4:
            logger.debug('NOTAM Date : %s', p[1])
            self.dates1.append(int(p[1]))
            logger.debug('NOTAM Date : %s', p[3])
            self.dates1.append(int(p[3]))
        if len(p) == 2:
            logger.debug('NOTAM Date : %s', p[1])
            logger.debug('Datelist1: reduction complete')
            self.dates1.append(int(p[1]))

    def p_datelist2(self, p):
        """datelist2 : DATE datelist2
                     | DATE AND DATE
                     | DATE
        """
        if len(p) == 3:
            p[0] = p[2]
            # Reduced Token needs to be added
            logger.debug('NOTAM Date : %s', p[1])
            self.dates2.append(int(p[1]))
        if len(p) == 4:
            logger.debug('NOTAM Date : %s', p[1])
            self.dates2.append(int(p[1]))
            logger.debug('NOTAM Date : %s', p[3])
            self.dates2.append(int(p[3]))
        if len(p) == 2:
            logger.debug('NOTAM Date : %s', p[1])
            logger.debug('Datelist2: reduction complete')
            self.dates2.append(int(p[1]))

    def p_daterange(self, p):
        """daterange : DATE RANGE DATE
        """
        logger.debug('daterange: stored dates=%s to %s.', p[1], p[3])
        self._store_dates = self._store_dates + range(int(p[1]), 1+int(p[3]))

    def p_daylist(self, p):
        """daylist : DAY daylist
                   | DAY AND DAY
                   | DAY
        """
        if len(p) == 3:
            p[0] = p[2]
            # Reduced Token needs to be added
            logger.debug('daylist: stored day=%s', p[1])
            self._store_weekdays.append(int(WEEK[p[1]]))
        if len(p) == 4:
            logger.debug('daylist: stored day=%s & day=%s', p[1], p[3])
            self._store_weekdays.append(int(WEEK[p[1]]))
            self._store_weekdays.append(int(WEEK[p[3]]))
        if len(p) == 2:
            logger.debug('daylist: stored day=%s', p[1])
            self._store_weekdays.append(int(WEEK[p[1]]))

    def p_timeslots(self, p):
        """timeslots : timerange timeslots
                     | timerange
        """
        if len(p) == 3:
            #logger.debug('timeslots: more timerange available')
            p[0] = p[2]
        else:
            logger.debug('timeslots: timerange reduction completed')

    def p_timerange(self, p):
        """timerange : HOUR RANGE HOUR
                     | SUNRISE RANGE HOUR
                     | HOUR RANGE SUNSET
                     | SUNRISE RANGE SUNSET
                     | H24
        """

        if len(p) == 4:
            if p[1] == 'SR':
                logger.debug('timerange: SR changed to "0000"')
                start_time = '0000'
            else:
                start_time = str(p[1])

            if p[3] == 'SS':
                logger.debug('timerange: SS changed to "2359"')
                stop_time = '2359'
            else:
                stop_time = str(p[3])
        else:
            logger.debug('timerange: H24 changed to "0000-2359"')
            start_time = '0000'
            stop_time = '2359'

        logger.debug('timerange: stored timedelta=(%s, %s)', start_time, stop_time)
        start_timedelta = datetime.timedelta(
            hours=int(start_time[0:2]),
            minutes=int(start_time[2:4])
            )
        stop_timedelta = datetime.timedelta(
            hours=int(stop_time[0:2]),
            minutes=int(stop_time[2:4])
            )
        self._store_timerange.append((start_timedelta, stop_timedelta))

    def p_exclusion(self, p):
        """exclusion : EXC exc_weekdays
        """
        logger.debug('exclusion: excluding day reduction completed')

    def p_exc_weekdays(self, p):
        """exc_weekdays : DAY exc_weekdays
                        | HOL exc_weekdays
                        | DAY
                        | HOL
        """

        logger.debug('exc_weekdays: excluding day %s', str(p[1]))
        self._store_exc_weekdays.append(WEEK[p[1]])
        if len(p) == 3:
            logger.debug('exc_weekdays: more weekdays to exclude')
            p[0] = p[2]

    def p_error(self, p):
        logger.error('Parsing error')
        logger.error(p)

    def _set_timeslice_initial_state(self, ref_month=''):
        '''Setting the timeslice in its initial state

            ref_month (str, optional): Defaults to ''. [description]
        '''

        if ref_month:
            logger.debug('Setting timeslice initial state')
        else:
            logger.debug('Setting timeslice initial state')
        # Internal temporary "store"
        self._store_month = '' # The latest month discovered by the parser
        self._store_dates = []
        self._store_timerange = []
        self._store_weekdays = []
        self._store_exc_weekdays = []
        self._store_timeslice = []
        self._store_multimonth = None

        self._ref_month = ref_month

        # Internal "state flags"
        self._day_mode = False
        self._multimonth = False
        #self._flag_sched_differed = False

    def _set_schedule_initial_state(self, notam_begin, notam_end):

        logger.debug('Setting schedule initial state')
        # Internal "store"
        self._store_schedule = []

        self._notam_begin = notam_begin
        self._notam_end = notam_end
        self._set_timeslice_initial_state(ref_month=notam_begin.month)

    def get_schedule(self):
        '''Retrieve the latest parsed schedule

        Returns:
            [list]: list of datetime tupple
        '''

        return self._store_schedule

    def __init__(self):
        '''Create a new Schedule parser object

        Constructor
        '''

        logger.info('ScheduleParser: new object creation')
        self.lexer = ScheduleLexer()
        self.tokens = self.lexer.tokens

        #self.parser = yacc.yacc(module=self, write_tables=0, debug=True)
        self.parser = yacc.yacc(module=self, write_tables=0, errorlog=yacc.NullLogger())
        logger.debug('ScheduleParser: LEX/YAC ready')

        # All _private attributes to store "partial" timeslot information & parser status flag
        self._store_month = '' # The latest month discovered by the parser
        self._store_dates = []
        self._store_timerange = []
        self._store_weekdays = []
        self._store_exc_weekdays = []
        self._store_timeslice = []
        self._store_multimonth = None

        self._day_mode = False
        self._flag_sched_differed = False
        self._multimonth = False

        self._notam_begin = None
        self._notam_end = None
        self._ref_month = None


        self._store_schedule = []

    def parse(self, notam_begin, notam_end, data):
        '''Execute the parsing to generate the expanded list of timeslots

        Args:
            notam_begin ([datetime]): the effective start of the NOTAM
            notam_end ([datetime]): the effective end of the NOTAM
            data ([string]): the schedule string to parse/expand into timeslot

        Returns:
            [list]: list of datetime tupple
        '''

        if data:
            self._set_schedule_initial_state(notam_begin, notam_end)

            logger.info('ScheduleParser: Parsing starting')
            logger.info('Args: %s', data)
            self.parser.parse(data, self.lexer.lexer, 0, 0, None)
            logger.info('ScheduleParser: Parsing completed')
            return self._store_schedule
        return []

if __name__ == '__main__':

    # We run our demo in DEBUG mode
    logging.basicConfig(level=logging.DEBUG)

    # Inspect is maybe better to build this type of string ?
    logger.info('<-- Module %s demo code -->', __file__)

    # Lexer is embedded in Parser but it can be usefull to validate this function directly
    # when debuging new schedule syntax for example
    sched_lexer = ScheduleLexer()

    # A wrong schedule string generating a Lexer exception
    sched_string_data = "JA 12 0900-1600, 13 0700-1800, 14-18 0700-1600, 19-20 0700-2200, 21 0700-1600, 22 0700-1500, 26 0800-2200, 27 0700-1600, 28 0700-2200 AND 29-31 0700-1600"
    try:
        sched_lexer.test(sched_string_data)
    except LexerWarning:
        logger.warning('ScheduleLexer stopped', exc_info=True)

    # A good schedule string that tokenize correctly
    sched_string_data = "JAN 12 0900-1600, 13 0700-1800, 14-18 0700-1600, 19-20 0700-2200, 21 0700-1600, 22 0700-1500, 26 0800-2200, 27 0700-1600, 28 0700-2200 AND 29-31 0700-1600"
    try:
        sched_lexer.test(sched_string_data)
    except LexerWarning:
        logger.debug('ScheduleLexer stopped', exc_info=True)

    # Schedule format supported:
    schedule_demos = [
        # A few possible schedule syntax that can be used for demo purpose ...
        # Feel free to experiment :-)
        # Note that it is best to set proper notam_begin/notam_end boundaries before calling the parser

        # Tested OK
        #'JAN 26-30 0730-1500',
        #'JAN 12 0900-1600, 13 0700-1800, 14-18 0700-1600, 19-20 0700-2200, 21 0700-1600, 22 0700-1500, 26 0800-2200, 27 0700-1600, 28 0700-2200 AND 29-31 0700-1600',
        #'DAILY SR-SS',
        #'DAILY 0700-1500 EXC SAT SUN',
        # 'DAILY 0530-2100',
        #'JAN 27 0900-0950 1800-1850, 28 1000-1050, 29 AND 30 1400-1450',
        #'FEB 17 AND 18 0900-1100 1230-1600',
        #'JAN 12 0900-1600, 13 0700-1800, 14-18 0700-1600, 19-20 0700-2200, 21 0700-1600, 22 0700-1500, 26 0800-2200, 27 0700-1600, 28 0700-2200 AND 29-31 0700-1600',
        #'FEB 03 10 19 24 0930-1100, 04 1130-1300 AND 05 11 0730-1300',
        #'MON-FRI 0630-1600',
        #'MON-FRI H24',
        #'MAR 31-APR 02 0730-1000 1130-1500 AND 03 0730-1000',
        'DAILY 0700-1500 EXC SAT SUN'
        # To be checked
        #'MAY 14 08:00 Till:PERM',
        #'JAN 15 09:34 Till:13 MAY 15 08:00 EST',
        #'MAR 31 AND APR 01-03 0630-1400',

        # Not supported yet !
        #'JAN 19 20 AND 27 SS-2100',
    ]

    # Parsing our schedule_demos

    # Parser is only created once
    test = ScheduleParser()
    for schedule_demo in schedule_demos:
        # Parser "state" is re-initialized when the parse method is called
        test.parse(notam_begin=datetime.datetime(2018, 3, 10), notam_end=datetime.datetime(2018, 3, 25), data=schedule_demo)
        logger.info('>>> Parsing summary:')
        logger.info('>>> "%s" extended to', schedule_demo)
        logger.info('>>> %s', test.get_schedule())
