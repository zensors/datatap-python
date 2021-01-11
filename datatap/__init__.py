"""
This module provides classes and methods for interacting with dataTap.  This includes inspecting individual annotations,
creating or importing new annotations, and creating or loading datasets for machine learning.

.. include:: ../README.md
"""

import sys as _sys

if _sys.version_info < (3, 7):
    print("\x1b[38;5;1mUsing an unsupported python version. Please install Python 3.7 or greater\x1b[0m")
    raise Exception("Invalid python version")

from .api.entities import Api

__all__ = [
    "Api",
    "api",
    "droplet",
    "geometry",
    "template",
    "utils",
]