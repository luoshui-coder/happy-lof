#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thin Python entrypoint.

Keep this thin so local Flask runs and optional WSGI adapters share one route table.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402,F401
