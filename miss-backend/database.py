# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import config
from models import Base

extra_args = {}
if "sqlite" in config.db_url:
    extra_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(config.db_url, **extra_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
