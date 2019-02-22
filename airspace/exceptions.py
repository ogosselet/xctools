class AixmSourceError(Exception):
    '''Exception class building a common message format including AIXM info

    Args:
        Exception (object): Exception as superclass

    '''

    def __init__(self, aixm_source, msg=None):
        '''Init the superclass "Exception" string

        Args:
            aixm_source ([AixmSource]): the AixmSource object where the exception was triggered
            msg ([str], optional): Defaults to None. The contextual message of the Exception
        '''

        if msg is None:
            # Set some default useful error message
            msg = 'unexpected error'
        exc_msg = 'AIXM {}: {}'.format(aixm_source.filename, msg)

        super(AixmSourceError, self).__init__(exc_msg)
        self.aixm_source = aixm_source


class AirspaceGeomUnknown(AixmSourceError):
    '''Exception raised when a AIXM decoding error is detected

    Args:
        AixmSourceError (Exception): AixmSourceError as superclass
    '''

    def __init__(self, aixm_source, msg=None):
        '''Init the superclass AixmSourceError message

        Args:
            aixm_source ([AixmSource]): the AixmSource object where the exception was triggered
            msg ([str], optional): Defaults to None (replaced by a generic message).
                The contextual message of the Exception
        '''

        if msg is None:
            msg = 'unknown geometry'
        super(AirspaceGeomUnknown, self).__init__(aixm_source, msg)
