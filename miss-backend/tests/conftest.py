# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import os
from unittest.mock import patch


def _mock_limit(*args, **kwargs):
    def decorator(func):
        return func
    return decorator


def pytest_configure(config):
    os.environ.setdefault("DB_URL", "sqlite:///./miss.db")
    p = patch("slowapi.Limiter.limit", _mock_limit)
    p.start()
    config._slowapi_patch = p


def pytest_unconfigure(config):
    p = getattr(config, "_slowapi_patch", None)
    if p is not None:
        p.stop()
