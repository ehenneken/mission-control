"""
Generic utilities for mission control
"""

import os
import time

from boto3.session import Session
from flask import current_app
from mc.exceptions import TimeOutError


def get_boto_session():
    """
    Gets a boto3 session using credentials stores in app.config; assumes an
    app context is active
    :return: boto3.session instance
    """
    return Session(
        aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY'),
        aws_secret_access_key=current_app.config.get('AWS_SECRET_KEY'),
        region_name=current_app.config.get('AWS_REGION')
    )


def timed(func, time_out=30, time_wait=1, exit_on=True):
    """
    Runs a function repeatedly until a it times out
    :param func: function to run
    :param time_out: time frame to run over
    :param time_wait: time to wait between each execution
    :param exit_on: boolean value to exit on
    :return:
    """
    counter = 0
    while func() != exit_on:
        time.sleep(time_wait)
        counter += 1
        if counter >= time_out:
            raise TimeOutError


class ChangeDir:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
