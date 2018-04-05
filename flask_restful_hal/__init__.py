# -*- coding: utf-8 -*-

from __future__ import absolute_import

from .api import Api
from .resource import Embedded, Link, Resource
from ._version import __version__, __version_info__  # noqa: F401

__all__ = ('Api', 'Embedded', 'Link', 'Resource')
