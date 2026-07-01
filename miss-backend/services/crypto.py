# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import os
import base64
import binascii
import logging
from cryptography.fernet import Fernet, InvalidToken

_cipher = None
_initialized = False

_LEGACY_PREFIX = b"PLAIN:"
_PREFIX = "ENC_V1_"


def init_fernet(key: str | None = None):
    global _cipher, _initialized
    if _initialized:
        return
    env_key = key or os.getenv("MISS_FERNET_KEY", "")
    if env_key:
        _cipher = Fernet(env_key.encode())
    else:
        _cipher = Fernet(Fernet.generate_key())
    _initialized = True
    logging.getLogger("crypto").info("Ferret cipher initialized (key persistent=%s)", bool(env_key))


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    if _cipher is None:
        init_fernet()
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
        if _cipher is None:
            init_fernet()
        return _cipher.decrypt(raw).decode()
    except InvalidToken:
        return text
