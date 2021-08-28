"""
pytest module: awstemp/awstemp.py
"""

from unittest.mock import call, mock_open, patch

import pytest

from awstemp import awstemp
from tests.helpers import data, mocks

ENCODING = "utf-8"


def raise_keyboard_interrupt():
    """Wrapper for lambdas to execute exceptions"""
    raise KeyboardInterrupt("INTERRUPT")


def test_init(instance):
    """Test the __init__ class function"""
    assert instance.config_path == data.AWS_CONFIG_FILE
    assert instance.credentials_path == data.AWS_SHARED_CREDENTIALS_FILE


def test_role_completer(instance):
    """Test that only roles are returned for correct completion"""
    assert instance.role_completer() == ["expired", "role1", "role2", "valid"]


def test_export_completer(instance):
    """Test that sorted credentials are returned for correct completion"""
    assert instance.export_completer() == [
        "default",
        "expired_temp",
        "role1",
        "role2",
        "valid_temp",
    ]


@pytest.mark.parametrize(
    "role,outcome",
    [
        ("default", False),
        ("role1", False),
        ("valid_temp", False),
        ("expired_temp", True),
        ("unknown", True),
    ],
    ids=[
        "default cannot expire",
        "role1 profile connot expire",
        "temporary credentials not expired",
        "temporary credentials expired",
        "Invalid credentials",
    ],
)
def test_is_expired(instance, role, outcome):
    """Test that credentials are considered expired correctly"""
    assert instance.is_expired(role) == outcome


@patch("builtins.open", new_callable=mock_open, read_data="data")
def test_clean(mock_file, instance):
    """Test that clean is not writing expired sections"""
    instance.syntax = lambda a: None
    instance.clean()

    assert mock_file.call_args_list == [
        call("AWS_SHARED_CREDENTIALS_FILE", "w", encoding=ENCODING),
        call("AWS_CONFIG_FILE", "w", encoding=ENCODING),
    ]

    for call_args in mock_file.mock_calls:
        assert call_args != call().write("[profile expired_temp]\n")
        assert call_args != call().write("[expired_temp]\n")


@patch("builtins.open", new_callable=mock_open, read_data="data")
def test_syntax(mock_file, instance):
    """Test that # vim syntax is added when not exists in file"""
    instance.syntax("path")

    assert call("path", "r", encoding=ENCODING) in mock_file.mock_calls
    assert call("path", "a", encoding=ENCODING) in mock_file.mock_calls
    assert call().write(awstemp.AWSTEMP.vimsyntax) in mock_file.mock_calls


@patch("builtins.open", new_callable=mock_open, read_data=awstemp.AWSTEMP.vimsyntax)
def test_syntax_skipped(mock_file, instance):
    """Test that # vim syntax is skipped added when exists in file"""
    instance.syntax("path")

    assert call("path", "r", encoding=ENCODING) in mock_file.mock_calls
    assert call("path", "a", encoding=ENCODING) not in mock_file.mock_calls
    assert call().write(awstemp.AWSTEMP.vimsyntax) not in mock_file.mock_calls


@patch("os.path.expanduser")
@patch("os.mkdir")
@patch("shutil.copy")
def test_backup(mock_shutil_copy, mock_os_mkdir, mock_os_path_expanduser, instance):
    """Test that the backup function calls correctly"""

    backup_dir = "BACKUP_DIR"
    mock_os_path_expanduser.return_value = backup_dir

    instance.backup()

    assert mock_os_mkdir.is_called_with(backup_dir)
    assert mock_shutil_copy.call_args_list == [
        call("AWS_SHARED_CREDENTIALS_FILE", f"{backup_dir}/credentials"),
        call("AWS_CONFIG_FILE", f"{backup_dir}/config"),
    ]


@pytest.mark.parametrize(
    "role,session",
    [
        (None, False),
        ("default", False),
        ("valid_temp", True),
    ],
    ids=[
        "None",
        "default",
        "temporary credentials with session token",
    ],
)
@patch("builtins.print")
def test_export(mock_print, instance, role, session):
    """Test export method for existing credentials"""
    instance.export(role)

    if role is None:
        role = "default"

    expected = [
        call(f"Profile: {role}"),
        call(f"export AWS_ACCESS_KEY_ID={data.AWS_ACCESS_KEY_ID}"),
        call(f"export AWS_SECRET_ACCESS_KEY={data.AWS_SECRET_ACCESS_KEY}"),
    ]

    if session:
        expected.append(call(f"export AWS_SESSION_TOKEN={data.AWS_SESSION_TOKEN}"))

    assert mock_print.call_args_list == expected


@patch("builtins.print")
def test_export_unknown(mock_print, instance):
    """Test export method for unknown credentials"""

    role = "unknown"

    with pytest.raises(SystemExit) as exception:
        instance.export(role)

    assert exception.value.code == 1
    assert mock_print.call_args_list == [call(f"Profile not found: {role}")]


@pytest.mark.parametrize(
    "role,expected",
    [(None, 0), ("default", 0), ("valid_temp", 0), ("expired_temp", 1)],
    ids=[
        "None",
        "default",
        "temporary credentials with session token",
        "temporary credentials with expired session token",
    ],
)
def test_status(instance, role, expected):
    """Test status method to check if credentials have expired"""
    with pytest.raises(SystemExit) as exception:
        instance.status(role)

    assert exception.value.code == expected


@patch("builtins.print")
def test_sessions(mock_print, instance):
    """Test sessions command lists expiry status of all temporary credentials"""
    instance.sessions()

    assert mock_print.call_args_list == [
        call("expired_temp (expired)"),
        call("valid_temp (59 minutes)"),
    ]


@patch("builtins.print")
def test_list(mock_print, instance):
    """Test list command lists credentials"""
    instance.list()

    assert mock_print.call_args_list == [
        call("default"),
        call("expired_temp (expired)"),
        call("role1"),
        call("role2"),
        call("valid_temp (59 minutes)"),
    ]


@pytest.mark.parametrize(
    "parameters",
    [
        (("valid", [], "skipping")),
        (("expired", ["AWS_SHARED_CREDENTIALS_FILE"], "created")),
        (("role1", ["AWS_CONFIG_FILE", "AWS_SHARED_CREDENTIALS_FILE"], "created")),
    ],
)
@patch("builtins.open", new_callable=mock_open, read_data="data")
def test_assume_without_mfa(mock_file, monkeypatch, instance, parameters):
    """Test assuming a role when credentials are already valid skips"""

    role = parameters[0]
    writes = parameters[1]
    expected = parameters[2]

    monkeypatch.setattr(*mocks.mock("boto3.Session", mocks.MockBotoSession()))

    instance.syntax = lambda a: None

    assert instance.assume(role) == expected
    assert mock_file.call_args_list == [call(x, "w", encoding=ENCODING) for x in writes]


@patch("builtins.input", lambda token: "TOKEN")
@patch("builtins.open", new_callable=mock_open, read_data="data")
def test_assume_with_mfa(mock_file, monkeypatch, instance):
    """Test assuming a role when credentials are already valid skips"""

    monkeypatch.setattr(*mocks.mock("boto3.Session", mocks.MockBotoSession()))

    instance.syntax = lambda path: None

    assert instance.assume("role2") == "created"
    assert mock_file.call_args_list == [
        call("AWS_CONFIG_FILE", "w", encoding=ENCODING),
        call("AWS_SHARED_CREDENTIALS_FILE", "w", encoding=ENCODING),
    ]


@patch("builtins.input", lambda token: raise_keyboard_interrupt())
def test_assume_with_mfa_interrupted(monkeypatch, instance):
    """Test assuming a role when credentials are already valid skips"""

    monkeypatch.setattr(*mocks.mock("boto3.Session", mocks.MockBotoSession()))

    with pytest.raises(SystemExit) as exception:
        assert instance.assume("role2")

    assert exception.value.code == 0
