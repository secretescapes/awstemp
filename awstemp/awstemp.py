#!/usr/bin/env python3
"""
Creates a temporary session for a given profile
"""

import datetime
import os
import shutil
import sys
import time
from configparser import ConfigParser

import boto3
import humanize
from dateutil.parser import parse


class AWSTEMP:
    """awstemp console command"""

    vimsyntax = "# vim: syntax=dosini\n"

    def __init__(self):
        """Constructer, load common files"""

        self.credentials_path = os.environ.get(
            "AWS_SHARED_CREDENTIALS_FILE", os.path.expanduser("~/.aws/credentials")
        )
        self.config_path = os.environ.get(
            "AWS_CONFIG_FILE", os.path.expanduser("~/.aws/config")
        )

        self.credentials = ConfigParser()
        self.credentials.read(self.credentials_path)

        self.config = ConfigParser()
        self.config.read(self.config_path)

    def role_completer(self, **_):
        """argcomplete completer for --role"""
        roles = [
            x.split()[1]
            for x in self.config.sections()
            if x != "default" and "_temp" not in x
        ]
        return sorted(roles)

    def export_completer(self, **_):
        """argcomplete completer for --export"""
        return sorted(self.credentials.sections())

    def is_expired(self, role):
        """Check if temporary role has expired"""

        if role not in self.credentials.sections():
            return True

        if not self.credentials.has_option(role, "aws_expiration"):
            return False

        expiry = datetime.datetime.fromisoformat(
            self.credentials.get(role, "aws_expiration")
        )
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        return now >= expiry

    def assume(self, role, alias=None):
        """Assumes Role and stores the temporary credentials"""

        if alias is None:
            alias = f"{role}_temp"

        if not self.is_expired(alias):
            return "skipping"

        credentials = self.credentials
        config = self.config

        print(f"Assuming role: {role} as {alias}")

        unix = int(time.time())

        cfg = {
            "region": config.get(
                f"profile {role}",
                "region",
                fallback=os.environ.get("AWS_DEFAULT_REGION", "eu-west-1"),
            ),
            "role_arn": config.get(f"profile {role}", "role_arn"),
            "mfa_serial": config.get(f"profile {role}", "mfa_serial", fallback=None),
            "session_name": f"{role}-{unix}",
            "source_profile": config.get(
                f"profile {role}", "source_profile", fallback="default"
            ),
        }

        sts = boto3.Session(profile_name=cfg["source_profile"]).client("sts")

        if cfg["mfa_serial"]:
            try:
                token = input("MFA Token: ")
            except KeyboardInterrupt:
                sys.exit(0)

            response = sts.assume_role(
                RoleArn=cfg["role_arn"],
                SerialNumber=cfg["mfa_serial"],
                RoleSessionName=cfg["session_name"],
                TokenCode=token,
            )

        else:
            response = sts.assume_role(
                RoleArn=cfg["role_arn"], RoleSessionName=cfg["session_name"]
            )

        config_section = f"profile {alias}"
        if config_section not in config.sections() and cfg["region"]:
            config.add_section(config_section)
            config.set(config_section, "region", cfg["region"])
            with open(self.config_path, "w") as config_file:
                config.write(config_file)

        if alias not in credentials.sections():
            credentials.add_section(alias)

        credentials.set(
            alias, "aws_access_key_id", response["Credentials"]["AccessKeyId"]
        )
        credentials.set(
            alias, "aws_secret_access_key", response["Credentials"]["SecretAccessKey"]
        )
        credentials.set(
            alias, "aws_session_token", response["Credentials"]["SessionToken"]
        )
        credentials.set(
            alias, "aws_expiration", response["Credentials"]["Expiration"].isoformat()
        )

        with open(self.credentials_path, "w") as credentials_file:
            credentials.write(credentials_file)

        self.syntax(self.config_path)
        self.syntax(self.credentials_path)

        print(f"Session credentials created as temporary profile: {alias}")

        return "created"

    def clean(self):
        """Iterate through sections and remove expired sections"""

        for section in self.credentials.sections():
            if self.is_expired(section):
                print(f"Removing expired: {section}")
                self.credentials.remove_section(section)

                if self.config.has_section(f"profile {section}"):
                    self.config.remove_section(f"profile {section}")

        with open(self.credentials_path, "w") as credentials_file:
            self.credentials.write(credentials_file)

        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)

        self.syntax(self.config_path)
        self.syntax(self.credentials_path)

    def syntax(self, path):
        """Add vim ini syntax if not exists"""

        with open(path, "r") as ini_file:
            data = ini_file.readlines()
        if self.vimsyntax not in data:
            with open(path, "a") as ini_file:
                ini_file.write(self.vimsyntax)

    def list(self):
        """List all credentials"""

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        for section in sorted(self.credentials.sections()):
            if self.credentials.has_option(section, "aws_session_token"):
                delta = parse(self.credentials.get(section, "aws_expiration")) - now
                if delta.total_seconds() > 0:
                    print(f"{section} ({humanize.naturaltime(-delta)[:-9]})")
                else:
                    print(f"{section} (expired)")
            else:
                print(section)

    def sessions(self):
        """List all sessions"""

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        for section in sorted(self.credentials.sections()):
            if self.credentials.has_option(section, "aws_session_token"):
                delta = parse(self.credentials.get(section, "aws_expiration")) - now
                if delta.total_seconds() > 0:
                    print(f"{section} ({humanize.naturaltime(-delta)[:-9]})")
                else:
                    print(f"{section} (expired)")

    def backup(self):
        """Backup credential and config files"""
        backup_dir = os.path.expanduser(
            f"~/.aws/backup-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        if not os.path.isdir(backup_dir):
            os.mkdir(backup_dir)
        shutil.copy(self.credentials_path, f"{backup_dir}/credentials")
        shutil.copy(self.config_path, f"{backup_dir}/config")
        print(f"Backup: {backup_dir}")

    def export(self, profile=None):
        """print export statements to console out"""

        if profile is None:
            profile = os.environ.get("AWS_PROFILE", "default")

        if profile not in self.credentials.sections():
            print(f"Profile not found: {profile}")
            sys.exit(1)

        print(f"Profile: {profile}")

        print(
            "export AWS_ACCESS_KEY_ID="
            + self.credentials.get(profile, "aws_access_key_id")
        )
        print(
            "export AWS_SECRET_ACCESS_KEY="
            + self.credentials.get(profile, "aws_secret_access_key")
        )
        if self.credentials.has_option(profile, "aws_session_token"):
            print(
                "export AWS_SESSION_TOKEN="
                + self.credentials.get(profile, "aws_session_token")
            )

    def status(self, profile=None):
        """Check if current profile is valid"""
        if profile is None:
            profile = os.environ.get("AWS_PROFILE", "default")
        if self.is_expired(profile):
            sys.exit(1)
        sys.exit(0)
