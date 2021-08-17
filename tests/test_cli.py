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
        "list",
        "sessions",
        "status",
    ]:
        assert subparser in subparsers
