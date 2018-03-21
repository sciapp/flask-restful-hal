# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import *  # noqa: F401,F403  pylint: disable=redefined-builtin,wildcard-import,unused-wildcard-import
from future import standard_library
standard_library.install_aliases()  # noqa: E402
try:
    from typing import Any, Callable, Dict, List, Optional, Union  # noqa: F401  # pylint: disable=unused-import
except ImportError:
    pass

from collections import OrderedDict
import flask_restful as rest
from flask_restful.representations.json import output_json
from flask import Flask, Blueprint  # noqa: F401  # pylint: disable=unused-import
from .representation import has_html_support, output_html
from .resource import Resource  # noqa: F401  # pylint: disable=unused-import


class Api(rest.Api):  # type: ignore
    def __init__(
        self,
        app=None,  # type: Optional[Union[Flask, Blueprint]]
        prefix='',  # type: str
        default_mediatype='application/hal+json',  # type: str
        decorators=None,  # type: Optional[List[Callable]]
        catch_all_404s=False,  # type: bool
        serve_challenge_on_401=False,  # type: bool
        url_part_order='bae',  # type: str
        errors=None,  # type: Optional[Dict]
        **kwargs  # type: Any
    ):
        # type: (...) -> None
        super().__init__(
            app, prefix, default_mediatype, decorators, catch_all_404s, serve_challenge_on_401, url_part_order, errors,
            **kwargs
        )
        self.representations = OrderedDict([('application/hal+json', output_json)])
        if has_html_support():
            self.representations['text/html'] = output_html

    def add_resource(self, resource, *urls, **kwargs):
        # type: (Resource, str, Any) -> None
        super().add_resource(resource, *urls, **kwargs)
        resource._primary_url = urls[0]  # pylint: disable=protected-access
