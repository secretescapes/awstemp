"""
Pytest reusable mock classes and functions
designed to work with monkeypatch
"""

import datetime

from tests.helpers import data


def mock(name, response):
    """hijack method mocker for use with monkeypatch"""

    def _mocker(*args, **kwargs):
        print(f"mocks.mock({name}: {args}, {kwargs} -> {response})")
        return response

    return name, _mocker


# pylint: disable=R0903
class MockBotoSession:
    """Mock class for boto3.Session"""

    class MockBotoSessionClient:
        """Mock class for boto3.Session.client"""

        assume_role_response = {
            "Credentials": {
                "AccessKeyId": data.AWS_ACCESS_KEY_ID,
                "SecretAccessKey": data.AWS_SECRET_ACCESS_KEY,
                "SessionToken": data.AWS_SESSION_TOKEN,
                "Expiration": (
                    datetime.datetime.now(tz=datetime.timezone.utc)
                    + datetime.timedelta(hours=1)
                ),
            }
        }

        def __init__(self, *args, **kwargs):
            """Initialisation method for boto3.Session.client mock object"""
            print(f"MockBotoSessionClient.__init__: {args}, {kwargs}")

        def assume_role(self, *args, **kwargs):
            """Mock boto3.Session.client("sts").assume_role"""
            print(f"MockBotoSessionClient.assume_role: {args}, {kwargs}")
            return self.assume_role_response

    def __init__(self, *args, **kwargs):
        """Initialisation method for boto3.Session object"""
        print(f"MockBotoSession.__init__: {args}, {kwargs}")

    def client(self, *args, **kwargs):
        """Mock boto3.Session.client"""
        return self.MockBotoSessionClient(*args, **kwargs)
