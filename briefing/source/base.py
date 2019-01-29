'''NOTAM briefing.source.base Module

Provides "public" method to define a simple and stable object interface and orchestrate
"_private" method that every specific source class should override to implement 
the specific business logic of the source

'''
from __future__ import absolute_import, division, print_function

import logging
import requests

logger = logging.getLogger(__name__)

class NotamSource(object):
    '''Briefing Source base class implementation

    Raises:
        NotImplementedError: raised if the child class has not implemented the overriding of the method
    '''


    def __init__(self):
        '''Do not overwrite this method unless you realize the impact of doing so
        '''

        # A requests session object
        self.req_session = requests.Session()
        self.parsed_briefing = []

    def login(self, username, password):
        '''Trigger the login operation required by the source.

        After the execution of this method, access to the source data should be possible.

        Args:
            username ([string]): credentials information
            password ([string]): credentials information
        '''

        logger.debug("Login to the source")
        self.username = username
        self.password = password
        self._login_sequence()

    def _login_sequence(self):
        '''Should be overrided to perform the business logic required to login a user 
        for the specific source.

        The full sequence required to login a user to a specific source.
        This could just be a "pass" if no login is required.

        Raises:
            NotImplementedError: raised if the child class has not implemented the overriding of the method
        '''

        raise NotImplementedError("User Login sequence not implemented for this source")

    def download_area_briefing(self, prefilter):
        '''Trigger the download of a briefing

        After the execution of this method, the raw briefing has been retrieved.

        Args:
            prefilter ([dict]): a dictionary with key/value supported by the source to filter NOTAM
                added to the briefing (see the specific source class documentation)
        '''

        #TODO: persist the raw data in the selected destination (local, s3, ...)
        logger.debug("Download area briefing")
        self.prefilter = prefilter
        self._download_area_briefing()

    def _download_area_briefing(self):
        '''Should be overrided to perform the business logic required to download a briefing for the specific source.

        Raises:
            NotImplementedError: exception raised if the method is not implemented in the specific source subclass
        '''

        raise NotImplementedError("Area briefing not available for this source")

    def parse_area_briefing(self):
        '''Trigger the parsing of the briefing raw data

        '''

        logger.debug("Parse area briefing")
        self._parse_area_briefing()

    def _parse_area_briefing(self):
        '''Should be overrided to perform the business logic required to parse the briefing raw data for the specific source.

        Raises:
            NotImplementedError: exception raised if the method is not implemented in the specific source subclass
        '''

        raise NotImplementedError("Area briefing parser not available for this source")

    def logout(self):
        '''Trigger the logout operation required by the source.

        After the execution of this method, the user access to the source data should not be possible.
        '''
        logger.debug("Logout from the source")
        self._logout()

    def _logout(self):
        '''Should be overrided to perform the business logic required to logout from the specific source.

        Raises:
            NotImplementedError: exception raised if the method is not implemented in the specific source subclass
        '''

        raise NotImplementedError("User Logout sequence not implemented for this source")

    def check_active_session(self):
        '''Test is there is a active session with the specific source

        Returns:
            Bool: True if there is an active session
        '''

        #TODO: This could be usefull if the program wants to create a persistent NotamSource object but that the session could timeout.
        #TODO: By checking pro-activly if the session is still active it might be better than having to react on an unexpected error
        return True


