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