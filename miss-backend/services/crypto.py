# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import os
import base64
import binascii
import logging
from cryptography.fernet import Fernet, InvalidToken

_env_key = os.getenv("MISS_FERNET_KEY", "")
if _env_key:
    _cipher = Fernet(_env_key.encode())
else:
    logging.getLogger("crypto").warning(
        "MISS_FERNET_KEY not set — encryption key will change on every restart. "
        "Old encrypted data will become unreadable."
    )
    _cipher = Fernet(Fernet.generate_key())

_LEGACY_PREFIX = b"PLAIN:"
_PREFIX = "ENC_V1_"


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    encrypted = _cipher.encrypt(plaintext.encode())
    return _PREFIX + base64.b64encode(encrypted).decode()


def decrypt(text: str) -> str:
    if not text:
        return text
    if not text.startswith(_PREFIX):
        return text
    text = text[len(_PREFIX):]
    try:
        raw = base64.b64decode(text)
    except (binascii.Error, ValueError) as e:
        logging.getLogger("crypto").debug("decrypt fallback to plaintext: %s", e)
        return text
    try:
        return _cipher.decrypt(raw).decode()
    except InvalidToken:
        return text
