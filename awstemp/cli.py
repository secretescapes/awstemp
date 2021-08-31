"""
CLI wrapper for awstemp package
"""
import argparse
import importlib.resources
import os
import sys

try:
    from importlib import metadata
except ImportError:  # pragma: no cover - 3.7 only
    import importlib_metadata as metadata  # pragma: no cover - 3.7 only

import argcomplete
import psutil

from awstemp import awstemp

INIT_MESSAGE = {
    "fish": (
        "# Load awstemp wrapper automatically by appending\n"
        "# the following to ~/.config/fish/config.fish:\n\n"
        "awstemp init - | source"
    ),
    "bash": (
        "# Load awstemp wrapper automatically by appending\n"
        "# the following to ~/.bash_profile:\n\n"
        'eval "$(awstemp init -)"'
    ),
    "zsh": (
        "# Load awstemp wrapper automatically by appending\n"
        "# the following to ~/.zshrc:\n\n"
        'eval "$(awstemp init -)"'
    ),
}


def arguments(cli):
    """Define CLI parameters"""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="name")

    assume_parser = subparsers.add_parser("assume", help="Assumes an AWS IAM role")
    assume_parser.add_argument(
        "role", type=str, help="Role to assume"
    ).completer = cli.role_completer
    assume_parser.add_argument(
        "alias",
        type=str,
        nargs="?",
        default=None,
        help="Alias to name the temporary profile",
    )

    backup_parser = subparsers.add_parser(
        "backup", help="Creates a backup of the credentials and config files"
    )
    backup_parser.set_defaults(func=cli.backup)

    list_parser = subparsers.add_parser(
        "clean", help="Cleans up expired session profiles"
    )
    list_parser.set_defaults(func=cli.clean)

    export_parser = subparsers.add_parser(
        "export", help="Exports the access keys to stdout"
    )
    export_parser.add_argument(
        "profile",
        type=str,
        nargs="?",
        default=None,
        help="Profile to export",
    ).completer = cli.export_completer

    init_parser = subparsers.add_parser(
        "init",
        help="Configure the shell environment for awstemp",
        description="Configure the shell environment for awstemp",
    )
    init_parser.add_argument(
        "-", dest="init", action="store_true", help="Return the wrapper source script"
    )
    init_parser.add_argument(
        "shell",
        nargs="?",
        default=None,
        help="Override shell detection. Supports `bash`, `zsh`, and `fish`",
    )

    list_parser = subparsers.add_parser("list", help="Lists the profiles available")
    list_parser.set_defaults(func=cli.list)

    status_parser = subparsers.add_parser(
        "status", help="Checks the status of the current profile"
    )
    status_parser.set_defaults(func=cli.status)

    sessions_parser = subparsers.add_parser(
        "sessions", help="Lists the session profiles and their TTL"
    )
    sessions_parser.set_defaults(func=cli.sessions)

    parser.add_argument(
        "-v", "--version", action="store_true", help="Show package version"
    )

    argcomplete.autocomplete(parser)
    return parser, parser.parse_args()


def get_shell(shell):
    """Get the parent shell"""
    if shell is None:
        shell = psutil.Process(os.getppid()).name()
    if shell in ["bash", "zsh", "fish"]:
        return shell
    print(f"{shell}: not supported")
    sys.exit(1)


def setup_shell(args):
    """Provide shell initialization"""

    shell = get_shell(args.shell)
    if not args.init:
        print(INIT_MESSAGE[shell])
    else:
        shell = "bash" if shell == "zsh" else shell
        print(importlib.resources.read_text("awstemp.wrappers", shell))


def main():
    """main function"""

    cli = awstemp.AWSTEMP()
    parser, args = arguments(cli)

    if args.version:
        print(f"awstemp {metadata.version('awstemp')}")
        sys.exit(0)

    if args.name == "assume":
        cli.assume(args.role, args.alias)
    elif args.name == "export":
        cli.export(args.profile)
    elif args.name in ["backup", "clean", "list", "status", "sessions"]:
        args.func()
    elif args.name == "init":
        setup_shell(args)
    else:
        parser.print_help()
        sys.exit(1)
