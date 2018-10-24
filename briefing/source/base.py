''' Notam Source Base Class

All method in this class should be implemented in the specific Notam source Class

'''

from __future__ import absolute_import, division, print_function

#from datetime import datetime, timedelta

import logging
import requests

logger = logging.getLogger(__name__)

class NotamSource(object):

    def __init__(self):
        # Do not overwrite __init__(self) unless you realize what you are doing :-)

        # A requests session object
        self.req_session = requests.Session()
        self.parsed_briefing = []

    def login(self, username, password):
        logger.debug("Login to the source")
        self.username = username
        self.password = password
        self._login_sequence()

    def _login_sequence(self):
        raise NotImplementedError("User Login sequence not implemented for this source")

    def download_area_briefing(self, prefilter):
        logger.debug("Download area briefing")
        self.prefilter = prefilter
        self._download_area_briefing()

    def _download_area_briefing(self):
        raise NotImplementedError("Area briefing not available for this source")

    def parse_area_briefing(self):
        logger.debug("Parse area briefing")
        self._parse_area_briefing()

    def _parse_area_briefing(self):
        raise NotImplementedError("Area briefing parser not available for this source")

    def logout(self):
        print("Logout from the source") #ToDo: replace with logging
        self._logout()

    def _logout(self):
        raise NotImplementedError("User Logout sequence not implemented for this source")

    def check_active_session(self):
        # Should return True or False if there is an active session
        # False if there is a timeout
        # This could be usefull for if a program wants to
        # create a persistent NotamSource object but that the session could
        # timeout, by checking pro-activly if the session is still active it
        # might be better than having to react on an unexpected error

        pass


