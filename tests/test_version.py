"""
Environment Setup Tests
"""

import os
import sys

PYTHON_MAJOR_VERSION = int(os.getenv("PYTHON_MAJOR_VERSION"))
PYTHON_MINOR_VERSION = int(os.getenv("PYTHON_MINOR_VERSION"))


def test_python_version():
    """
    Simple tester to ensure that toxi is using the right environment
    when testing. Don't ask, it was a pain to setup.
    """

    assert sys.version_info.major == PYTHON_MAJOR_VERSION
    assert sys.version_info.minor == PYTHON_MINOR_VERSION
