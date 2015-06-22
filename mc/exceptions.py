"""
Custom exceptions
"""


class NoSignatureInfo(Exception):
    """
    Raised when no signature info is found
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class InvalidSignature(Exception):
    """
    Raised when the signature is not validated
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class BuildError(Exception):
    """
    Raised when a build does not complete successfully
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class UnknownRepoError(Exception):
    """
    Raised when a repo is not known to mc
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class UnknownServiceError(Exception):
    """
    Raised when a service is not known to mc
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)