"""Validate CSV upload bytes before parsing or writing them."""

import base64
import binascii
import uuid
from pathlib import Path

from services.runtime_service import MAX_UPLOAD_BYTES


def decode_csv_upload(contents: str, filename: str | None) -> bytes:
    if not filename or not filename.lower().endswith(".csv"):
        raise ValueError("Choose a CSV file.")
    if not isinstance(contents, str) or "," not in contents:
        raise ValueError("The upload is incomplete. Choose the file again.")
    header, encoded = contents.split(",", 1)
    if not header.startswith("data:") or not header.endswith(";base64"):
        raise ValueError("The upload format is invalid.")
    if len(encoded) > 4 * ((MAX_UPLOAD_BYTES + 2) // 3):
        raise ValueError("The CSV file is too large. The limit is 20 MB.")
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("The upload could not be read. Choose the file again.") from exc
    if not decoded or len(decoded) > MAX_UPLOAD_BYTES:
        raise ValueError("Choose a non-empty CSV file of up to 20 MB.")
    return decoded


def save_csv_upload(contents: str, filename: str, directory: Path) -> Path:
    decoded = decode_csv_upload(contents, filename)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid.uuid4().hex}.csv"
    with path.open("xb") as handle:
        handle.write(decoded)
    return path
