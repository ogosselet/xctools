###
# Retrieves the NOTAM from a specific source

# The sequence is the following

# - login (including confirmation)
# - pre_fetch (prepare filters, ) 
# - fetch ( )
# - post_fetc
from __future__ import absolute_import, division, print_function
import logging
import datetime

from requests import Session

from briefing.source.nats import NATS
from notam.notam import Notam, DecodingError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    logger.info("Starting NOTAM retriever")

    logger.debug("Source: NATS")
    nats_test = NATS()

    # ToDO: Embbed the login_sequence in the object creation ?
    # Means we only get a NATS object that we can use to retrieve information if the 
    # login_sequence was completed successfully

    # logged_in = nats_test.login("source_username", "source_password")
    logger.debug("NATS: User logged in")

    prefilter = {
        'lower_fl': '0',
        'upper_fl': '999',
    #   'ifr': True,
        'vfr': True,
    #   'fancy_key': "blah",
        'firs': ['EBBU', 'LFFF'],
        'utc_from': datetime.datetime(2018, 9, 12, 12, 0),
        'utc_to': datetime.datetime(2018, 9, 12, 17, 0)
    }

    # The source of the data is an "offline" file for dev only.
    # out = nats_test.download_area_briefing(prefilter)
    file_briefing = open("briefing/source/tests/nats.html", "r")
    nats_test.raw_area_briefing = file_briefing.read().encode('utf-8')
    file_briefing.close()

    nats_test.parse_area_briefing()
    for notam in nats_test.parsed_briefing:
        print(notam)
        try:
            nt = Notam(notam)
            print('{} - {} - {}'.format(nt.reference, nt. full_q_line, nt.scope))
        except DecodingError as warn:
            logger.error(warn)
        except Exception:
            logger.error('Major error building a NOTAM object', exc_info=True)
        #print(nt)

except Exception:
    logging.error("NOTAM retriever failure", exc_info=True)    


