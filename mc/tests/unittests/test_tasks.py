"""
Test utilities
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(PROJECT_HOME)

import unittest

from mc import tasks

class TestBuilder(unittest.TestCase):
    """
    Test the Build task
    """

    def test_builder(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)