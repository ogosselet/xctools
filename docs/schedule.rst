Schedule Parser Module
======================

Expand the semantic version of a Notam Schedule into a list of datetime tupples representing all the relevant timeslots of the Notam.

Usage
-----

>>> from sched_parser import ScheduleParser
>>>
>>> import datetime
>>>
>>> notam_schedule = 'MAR 31-APR 02 0730-1000 1130-1500 AND 03 0730-1000'
>>> notam_start_date = datetime.datetime(2018, 3, 31)
>>> notam_end_date = datetime.datetime(2018, 4, 3)
>>>
>>> parser = ScheduleParser()
>>> parser.parse(notam_start_date, notam_end_date, notam_schedule)
[(datetime.datetime(2018, 3, 31, 7, 30), datetime.datetime(2018, 3, 31, 10, 0)), (datetime.datetime(2018, 3, 31, 11, 30), datetime.datetime(2018, 3, 31, 15, 0)), (datetime.datetime(2018, 4, 1, 7, 30), datetime.datetime(2018, 4, 1, 10, 0)), (datetime.datetime(2018, 4, 1, 11, 30), datetime.datetime(2018, 4, 1, 15, 0)), (datetime.datetime(2018, 4, 2, 7, 30), datetime.datetime(2018, 4, 2, 10, 0)), (datetime.datetime(2018, 4, 2, 11, 30), datetime.datetime(2018, 4, 2, 15, 0)), (datetime.datetime(2018, 4, 3, 7, 30), datetime.datetime(2018, 4, 3, 10, 0))]

