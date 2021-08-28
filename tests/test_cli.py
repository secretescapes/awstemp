"""
pytest module: awstemp/cli.py
"""

import argparse
from unittest.mock import Mock, call, patch

import pytest

import awstemp


@pytest.mark.parametrize(
    "name",
    [
        None,
        "invalid",
    ],
)
@patch("awstemp.cli.arguments")
def test_main_print_help(mock_cli_arguments, name):
    """Tests that the parser print function is called"""

    mock_parse_args = Mock()
    mock_parse_args.name = name
    mock_parser = Mock()
    mock_parser.print_help = Mock()

    mock_cli_arguments.return_value = (mock_parser, mock_parse_args)

    with pytest.raises(SystemExit) as exception:
        awstemp.cli.main()

    assert exception.value.code == 1
    assert mock_parser.print_help.call_args_list == [call()]


@pytest.mark.parametrize("name", ["backup", "clean", "list", "status", "sessions"])
@patch("awstemp.cli.arguments")
def test_main_calls_func(mock_cli_arguments, name):
    """Tests that generic none parametrized functions are called"""

    mock_parse_args = Mock()
    mock_parse_args.name = name
    mock_parse_args.func = Mock()

    mock_cli_arguments.return_value = (None, mock_parse_args)

    awstemp.cli.main()

    assert mock_parse_args.func.call_args_list == [call()]


@patch("awstemp.cli.arguments")
@patch("awstemp.awstemp.AWSTEMP")
def test_main_calls_cli_export(mock_awstemp_awstemp, mock_cli_arguments):
    """Tests that the cli export command is called"""

    mock_parse_args = Mock()
    mock_parse_args.name = "export"
    mock_parse_args.profile = "profile"

    mock_awstemp = Mock()
    mock_awstemp.export = Mock()

    mock_cli_arguments.return_value = (None, mock_parse_args)
    mock_awstemp_awstemp.return_value = mock_awstemp

    awstemp.cli.main()

    assert mock_awstemp.export.call_args_list == [call(mock_parse_args.profile)]


@patch("awstemp.cli.setup_shell")
@patch("awstemp.cli.arguments")
def test_main_calls_cli_init(mock_cli_arguments, mock_cli_setup_shell):
    """Tests that the cli export command is called"""

    mock_parse_args = Mock()
    mock_parse_args.name = "init"

    mock_cli_arguments.return_value = (None, mock_parse_args)

    awstemp.cli.main()

    assert mock_cli_setup_shell.call_args_list == [call(mock_parse_args)]


@patch("awstemp.cli.arguments")
@patch("awstemp.awstemp.AWSTEMP")
def test_main_calls_cli_assume(mock_awstemp_awstemp, mock_cli_arguments):
    """Tests that the cli assume command is called"""

    mock_parse_args = Mock()
    mock_parse_args.name = "assume"
    mock_parse_args.role = "role"
    mock_parse_args.alias = "alias"

    mock_awstemp = Mock()
    mock_awstemp.assume = Mock()

    mock_cli_arguments.return_value = (None, mock_parse_args)
    mock_awstemp_awstemp.return_value = mock_awstemp

    awstemp.cli.main()

    assert mock_awstemp.assume.call_args_list == [
        call(mock_parse_args.role, mock_parse_args.alias)
    ]


def test_arguments():
    """Test that the expected commands are registered"""

    parser, _ = awstemp.cli.arguments(Mock())

    subparsers = []

    # pylint: disable=W0212
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for subparser in action.choices.keys():
                subparsers.append(str(subparser))

    for subparser in [
        "assume",
        "backup",
        "clean",
        "export",
        "init",
        "list",
        "sessions",
        "status",
    ]:
        assert subparser in subparsers


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
@patch("psutil.Process.name")
def test_get_shell(mock_psutil_process_name, shell):
    """Test parent shell detection"""
    mock_psutil_process_name.return_value = shell
    assert awstemp.cli.get_shell(None) == shell


def test_get_shell_force():
    """Test parent shell forced"""
    shell = "bash"
    assert awstemp.cli.get_shell(shell) == shell


def test_get_shell_unknown():
    """Test parent shell detection exits on unhandled shell unknown"""
    with pytest.raises(SystemExit) as exception:
        awstemp.cli.get_shell("unhandled")
    assert exception.value.code == 1


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
@patch("awstemp.cli.get_shell")
@patch("builtins.print")
def test_setup_shell_message(mock_print, mock_awstemp_cli_get_shell, shell):
    """Test shell setup init message is correct"""
    mock_awstemp_cli_get_shell.return_value = shell
    args = Mock()
    args.init = None
    args.shell = shell
    awstemp.cli.setup_shell(args)

    assert mock_print.call_args_list == [call(awstemp.cli.INIT_MESSAGE[shell])]


@pytest.mark.parametrize(
    "shell,expected", [("bash", "bash"), ("zsh", "bash"), ("fish", "fish")]
)
@patch("awstemp.cli.get_shell")
@patch("importlib.resources.read_text")
def test_setup_shell_wrapper(
    mock_read_text, mock_awstemp_cli_get_shell, shell, expected
):
    """Test shell setup returns correct wrapper script"""
    mock_awstemp_cli_get_shell.return_value = shell
    args = Mock()
    args.init = True
    args.shell = shell
    awstemp.cli.setup_shell(args)

    assert mock_read_text.call_args_list == [call("awstemp.wrappers", expected)]
