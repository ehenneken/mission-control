"""
Views
"""
import hmac
import hashlib

from flask import current_app, request, abort
from flask.ext.restful import Resource

from mc.exceptions import NoSignatureInfo, InvalidSignature
from mc.models import db, Commit
from mc.tasks import build_docker


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
            current_app.config['GITHUB_SECRET'],
            msg=request.data,
            digestmod=hashlib.__getattribute__(digestmod),
        )

        if h.hexdigest() != sig:
            raise InvalidSignature("Signature not validated")

        return True

    @staticmethod
    def parse_github_payload(request=None):
        """
        parses a github webhook message to create a models.Commit instance
        :param request: request containing the header and body
        :return: models.Commit based on the incoming payload
        """

        if request is None:
            raise ValueError("No request object given")

        payload = request.get_json()

        return Commit(
            commit_hash=payload['head_commit']['id'],
            timestamp=payload['head_commit']['timestamp'],
            author=payload['head_commit']['author']['username'],
            repository=payload['repository']['name'],
        )

    def post(self):
        """
        Parse the incommit commit message, save to the backend database, and
        create a build.
        This endpoint should be contacted by a github webhook.
        """

        try:
            GithubListener.verify_github_signature(request)
        except (NoSignatureInfo, InvalidSignature) as e:
            current_app.logger.warning("{}: {}".format(request.remote_addr, e))
            abort(400)

        commit = GithubListener.parse_github_payload(request)
        db.session.add(commit)
        db.session.commit()
        build_docker.delay(commit)
        return {"build": "{}:{}".format(commit.repository, commit.commit_hash)}











