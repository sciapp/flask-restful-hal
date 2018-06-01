# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import *  # noqa: F401,F403  pylint: disable=redefined-builtin,wildcard-import,unused-wildcard-import
from future import standard_library
standard_library.install_aliases()  # noqa: E402
try:
    from typing import Any, Dict, List, Match, Optional, Tuple, Union  # noqa: F401  # pylint: disable=unused-import
except ImportError:
    pass

import re
import flask_restful as rest
import sys
from flask_restful.reqparse import RequestParser
from urllib.parse import quote as urllib_quote


class Embedded:
    def __init__(self, rel, resource, *params_list, **kwargs):
        # type: (str, Resource, Union[Dict, Tuple], bool) -> None
        self._rel = rel
        self._resource = resource
        self._params_list = params_list
        self._always_as_list = kwargs.get('always_as_list', False)

    @property
    def rel(self):
        # type: () -> str
        return self._rel

    @property
    def resource(self):
        # type: () -> Resource
        return self._resource

    @property
    def params_list(self):
        # type: () -> Tuple[Union[Dict, Tuple], ...]
        return self._params_list

    @property
    def has_data(self):
        # type: () -> bool
        return len(self._params_list) > 0

    def data(self, embed=0, include_links=True):
        # type: (int, bool) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]
        if len(self._params_list) > 1 or (self._always_as_list and self._params_list):
            resource_instance = self._resource()
            return [
                resource_instance.to_dict(*params, embed=embed - 1, include_links=include_links)
                if isinstance(params, (list, tuple)) else
                resource_instance.to_dict(embed=embed - 1, include_links=include_links, **params)
                for params in self._params_list
            ]
        elif len(self._params_list) == 1:
            params = self._params_list[0]
            resource_instance = self._resource()
            if isinstance(params, (list, tuple)):
                return resource_instance.to_dict(*params, embed=embed - 1, include_links=include_links)
            else:
                return resource_instance.to_dict(embed=embed - 1, include_links=include_links, **params)
        else:
            return None


class Link:
    def __init__(self, rel, *links, **kwargs):
        # type: (str, Union[Tuple[str, Dict[str, str]], str], bool) -> None
        self._rel = rel
        self._always_as_list = kwargs.get('always_as_list', False)
        self._quote = kwargs.get('quote', True)
        self._links = []  # type: List[Dict[str, str]]
        for link in links:
            link_dict = self._create_link_dict(link)
            self._links.append(link_dict)

    def _create_link_dict(self, link):
        # type: (Union[Tuple[str, Dict[str, str]], str]) -> Dict[str, str]
        if isinstance(link, (list, tuple)):
            href, extra_attributes = link
        else:
            href, extra_attributes = link, {}
        link_dict = {'href': urllib_quote(href) if self._quote else href}
        link_dict.update(extra_attributes)
        return link_dict

    @property
    def rel(self):
        # type: () -> str
        return self._rel

    @property
    def link(self):
        # type: () -> Optional[Union[List[Dict[str, str]], Dict[str, str]]]
        if len(self._links) > 1 or (self._always_as_list and self._links):
            return self._links
        elif len(self._links) == 1:
            return self._links[0]
        else:
            return None


class Resource(rest.Resource):  # type: ignore
    _request_parser = RequestParser()
    _request_parser.add_argument('embed')
    _request_parser.add_argument('links')

    def to_dict(self, *args, **kwargs):
        # type: (str, Any) -> Dict[str, Any]
        def extract_keywords_from_url(url):
            # type: (str) -> List[str]
            found_keywords = []  # type: List[str]

            def save_found_keyword(match_obj):
                # type: (Match[str]) -> str
                found_keywords.append(match_obj.group(1))
                return match_obj.group(0)

            re.sub(r'<(?:[^:>]*:)?([^>]*)>', save_found_keyword, url)
            return found_keywords

        def merge_args_and_kwargs(*args, **kwargs):
            # type: (str, str) -> Dict[str, str]
            url_keywords = extract_keywords_from_url(self._primary_url)
            merged_kwargs = {url_keyword: arg for url_keyword, arg in zip(url_keywords, args)}  # type: Dict[str, str]
            merged_kwargs.update(kwargs)
            # cheroot / CherryPy unquotes URLs but not ``%2F`` which is the path separator -> unquote it explicitly
            # see https://github.com/cherrypy/cheroot/blob/v6.0.0/cheroot/server.py#L826 for more explanation
            for url_keyword in url_keywords:
                merged_kwargs[url_keyword] = '/'.join(re.split(r'%2F', merged_kwargs[url_keyword], flags=re.IGNORECASE))
            return merged_kwargs

        def add_links(resource, **kwargs):
            # type: (Dict[str, Any], str) -> None
            def substitute(match_obj):
                # type: (Match[str]) -> str
                keyword = match_obj.group(1)
                return urllib_quote(kwargs[keyword], safe='')

            self_link = Link('self', re.sub(r'<(?:.*:)?([^>]*)>', substitute, self._primary_url), quote=False)
            resource['_links'] = {self_link.rel: self_link.link}
            try:
                links = self.links(**kwargs)
            except AttributeError:
                return
            if links is None:
                return
            if isinstance(links, Link):
                links = [links]
            links = [link for link in links if link.link is not None]
            resource['_links'].update({link.rel: link.link for link in links})

        def embed_resources(resource, **kwargs):
            # type: (Dict[str, Any], str) -> None
            try:
                embeddeds = self.embedded(**kwargs)
            except AttributeError:
                return
            if embeddeds is None:
                return
            if isinstance(embeddeds, Embedded):
                embeddeds = [embeddeds]
            embeddeds = [embedded for embedded in embeddeds if embedded.has_data]
            resource['_embedded'] = {}
            resource['_embedded'].update({embedded.rel: embedded.data(embed, include_links) for embedded in embeddeds})

        embed = kwargs.get('embed', 0)  # type: int
        include_links = kwargs.get('include_links', True)  # type: bool
        for key in ('embed', 'include_links'):
            del kwargs[key]
        merged_kwargs = merge_args_and_kwargs(*args, **kwargs)
        data = self.data(**merged_kwargs)
        resource = dict(data if data is not None else ())
        if include_links:
            add_links(resource, **merged_kwargs)
        if embed > 0:
            embed_resources(resource, **merged_kwargs)
        return resource

    def get(self, **kwargs):
        # type: (str) -> Dict[str, Any]
        def parse_args():
            # type: () -> Tuple[int, bool]
            def is_valid_true_string(string):
                # type: (str) -> bool
                return string is not None and string.lower() in ('true', 'yes', '1', 't', 'y')

            args = self._request_parser.parse_args()
            if args['embed'] is not None and args['embed'].isdigit():
                embed = int(args['embed'])
            else:
                embed = sys.maxsize if is_valid_true_string(args['embed']) else 0
            links = is_valid_true_string(args['links'])
            return embed, links

        embed, include_links = parse_args()
        if hasattr(self, 'pre_hal') and callable(self.pre_hal):
            self.pre_hal(embed=embed, include_links=include_links, **kwargs)
        return self.to_dict(embed=embed, include_links=include_links, **kwargs)
