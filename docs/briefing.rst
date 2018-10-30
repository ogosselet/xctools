Briefing Module
===============

Download a Pre-Flight Information Bulletins (PIB) containing published NOTAMs, parse the briefing and create a list of dictionary representation of the NOTAM.
The resulting data can be used to create `XCTools Notam <./code.html#notam.notam.Notam>`_ objects.

XCTools target to support multiple sources to ensure:

- information reliability: a source might provide more precise information for a specific region (FIRs) of interest
- service continuity: it is possible that a source change the format of the data and that the XCTools community needs some time to rework the relevant module

=> it is required to be able to switch an application to an alternate source of briefing.

We expect contributions from the community if other sources are required.

NATS Source
-----------

The `NATS <http://www.nats-uk.ead-it.com/public/index.php.html>`_ is a UK based company providing Aeronautical Information Services.

NATS has proven to be a stable and reliable source of PIB information since we use it (2015).
Access to the NOTAM information requires user website registration.

Usage
^^^^^

>>> from briefing.source.nats import NATS
>>> import datetime
>>>
>>> nats_source = NATS()
>>> # Change this with your own NATS credentials
>>> nats_source.login("username", "password")
>>>
>>> # See Notes for prefilter details
>>> prefilter = { \
>>>    'lower_fl': '0', \
>>>    'upper_fl': '999', \
>>>    'vfr': True, \
>>>    'firs': ['EBBU', 'LFFF'], \
>>>    'utc_from': datetime.datetime(2018, 10, 31, 12, 0), \
>>>    'utc_to': datetime.datetime(2018, 10, 31, 14, 30) \
>>>    }
>>>
>>> # Area Briefing download
>>> nats_source.download_area_briefing(prefilter)
>>>
>>> print(nats_source.raw_area_briefing)
>>> # the downloaded raw area briefing in html
>>>
>>> # Area Briefing parsing
>>> nats_source.parse_area_briefing()
>>>
>>> # Normalized list of NOTAMs
>>> nats_source.parsed_briefing
[{'a': '', 'upper': '', 'c': '18/12/20 09:00 EST', 'b': '18/10/05 13:13', 'e': 'ATS ROUTE UL745 CLSD', 'src': 'NATS', 'lower': '', 'q': 'EBBU/QARLC/IV/NBO/E/195/660/5130N00326E010', 'sched': '', 'ref': 'A3099/18'}]

Notes
^^^^^

* the prefilter fields available are source specific
    *  `NATS prefilter (see Other Parameters) <./code.html#briefing.source.nats.NATS>`_

Other sources
-------------

Other interesting source of NOTAM data to develop

- `SIA <http://notamweb.aviation-civile.gouv.fr/>`_
- `Laminar Data <https://developer.laminardata.aero/documentation/notamdata/v2>`_


