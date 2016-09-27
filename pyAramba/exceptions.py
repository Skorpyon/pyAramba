# -*- coding: utf-8 -*-


class ArambaError(Exception):
    pass


class ArambaEngineError(ArambaError):
    pass


class ArambaValueError(ArambaError):
    pass


class ArambaAPIError(ArambaError):

    def __init__(self, message, status_code, *args, **kwargs):
        self.message = message
        self.status_code = status_code
        super(ArambaAPIError, self).__init__(message, *args, **kwargs)