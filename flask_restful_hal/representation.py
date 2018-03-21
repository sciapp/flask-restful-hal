# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import *  # noqa: F401,F403  pylint: disable=redefined-builtin,wildcard-import,unused-wildcard-import
from future import standard_library
standard_library.install_aliases()  # noqa: E402

from flask import make_response
try:
    from json2html import json2html
    _has_html_support = True
except ImportError:
    _has_html_support = False


def has_html_support():
    return _has_html_support


def output_html(data, code, headers=None):
    html_document = '''
<!DOCTYPE html>
<html>
<body>
{}
</body>
</html>
'''.format(json2html.convert(data)).strip()
    resp = make_response(html_document, code)
    resp.headers.extend(headers or {})
    return resp
