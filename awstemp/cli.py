"""
CLI wrapper for awstemp package
"""
import argparse
import sys

import argcomplete

from awstemp import awstemp


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
        "clean", help="cleans up expired session profiles"
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

    argcomplete.autocomplete(parser)
    return parser, parser.parse_args()


def main():
    """main function"""

    cli = awstemp.AWSTEMP()
    parser, args = arguments(cli)

    if args.name == "assume":
        cli.assume(args.role, args.alias)
    elif args.name == "export":
        cli.export(args.profile)
    elif args.name in ["backup", "clean", "list", "status", "sessions"]:
        args.func()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborting...")
