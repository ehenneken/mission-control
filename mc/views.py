"""
Views
"""
from flask import current_app, request
from flask.ext.restful import Resource
import hmac
import hashlib
from mc.exceptions import NoSignatureInfo, InvalidSignature


class GithubListener(Resource):
    """
    github webhook logic and routes
    """

    @staticmethod
    def verify_github_signature(request=None):
        """
        Validates the github webhook signature

        :param request containing the header and body
        :type: flask.request object or None
        :return: None or raise
        """

        if request is None:
            raise NoSignatureInfo("No request object given")

        sig = request.headers.get(
            current_app.config.get('GITHUB_SIGNATURE_HEADER')
        )

        if sig is None:
            raise NoSignatureInfo("No signature header found")

        digestmod, sig = sig.split('=')

        h = hmac.new(
            current_app.config['SECRET_KEY'],
            msg=request.data,
            digestmod=hashlib.__getattribute__(digestmod),
        )

        if h.hexdigest() != sig:
            raise InvalidSignature("Signature not validated")

        return True







