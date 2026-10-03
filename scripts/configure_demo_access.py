"""Create the Oracle service login without storing a plain password."""

import argparse
import getpass
import os
import re
from pathlib import Path

from werkzeug.security import generate_password_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    username = input("Demo username [demo]: ").strip() or "demo"
    if not re.fullmatch(r"[A-Za-z0-9._-]+", username):
        raise SystemExit("Use letters, numbers, dots, underscores, or dashes for the username.")
    password = getpass.getpass("Demo password (at least 12 characters): ")
    if len(password) < 12:
        raise SystemExit("Use a password of at least 12 characters.")
    if password != getpass.getpass("Repeat the password: "):
        raise SystemExit("Passwords did not match.")
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.destination, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.chmod(args.destination, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(f'S2COOL_AUTH_USER="{username}"\n')
        handle.write(f'S2COOL_PASSWORD_HASH="{generate_password_hash(password)}"\n')
    print("Demo login saved. Restart s2cool.service after changing this file.")


if __name__ == "__main__":
    main()
