"""
This module provides classes and methods for interacting with dataTap.  This includes inspecting individual annotations,
creating or importing new annotations, and creating or loading datasets for machine learning.

.. include:: ../README.md
"""

from .api.entities import Api

__all__ = [
    "Api",
    "api",
    "droplet",
    "geometry",
    "template",
    "utils",
]