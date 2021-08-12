"""
pytest conftest.py file for testing hooks and fixtures
"""

import datetime
from configparser import ConfigParser

import pytest

from awstemp import awstemp
from tests.helpers import data


@pytest.fixture(name="instance", autouse=True)
def fixture_instance(monkeypatch):
    """
    Fixture to create a patched instance of the AWSTEMP class
    """

    mock_config = ConfigParser()
    mock_config["default"] = {}
    mock_config["profile role1"] = {
        "role_arn": data.ROLE_ARN,
    }
    mock_config["profile role2"] = {
        "mfa_serial": data.MFA_SERIAL,
        "role_arn": data.ROLE_ARN,
    }
    mock_config["profile valid"] = {
        "role_arn": data.ROLE_ARN,
    }
    mock_config["profile expired"] = {
        "role_arn": data.ROLE_ARN,
    }
    mock_config["profile valid_temp"] = {}
    mock_config["profile expired_temp"] = {}

    mock_credentials = ConfigParser()
    mock_credentials["default"] = {
        "aws_access_key_id": data.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": data.AWS_SECRET_ACCESS_KEY,
    }
    mock_credentials["role1"] = {}
    mock_credentials["role2"] = {}
    mock_credentials["valid_temp"] = {
        "aws_access_key_id": data.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": data.AWS_SECRET_ACCESS_KEY,
        "aws_session_token": data.AWS_SESSION_TOKEN,
        "aws_expiration": (
            datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(hours=1)
        ).isoformat(),
    }
    mock_credentials["expired_temp"] = {
        "aws_access_key_id": data.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": data.AWS_SECRET_ACCESS_KEY,
        "aws_session_token": data.AWS_SESSION_TOKEN,
        "aws_expiration": "2021-07-29T16:18:13+00:00",
    }

    monkeypatch.setenv("AWS_CONFIG_FILE", data.AWS_CONFIG_FILE)
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", data.AWS_SHARED_CREDENTIALS_FILE)

    patched_instance = awstemp.AWSTEMP()
    patched_instance.config = mock_config
    patched_instance.credentials = mock_credentials

    yield patched_instance
