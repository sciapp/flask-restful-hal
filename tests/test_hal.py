# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import *  # noqa: F401,F403  pylint: disable=redefined-builtin,wildcard-import,unused-wildcard-import
from future import standard_library
standard_library.install_aliases()  # noqa: E402

import pytest
from flask import Flask, url_for
from flask_restful_hal import Api, Embedded, Link, Resource

TODOS = {
    'todo1': {
        'task': 'build an API'
    },
    'todo2': {
        'task': '?????'
    },
    'todo3': {
        'task': 'profit!'
    },
}


class Todo(Resource):
    @staticmethod
    def data(todo):
        return TODOS[todo]

    @staticmethod
    def links(todo):
        return Link('collection', '/todos')


class TodoList(Resource):
    @staticmethod
    def data():
        return {'size': len(TODOS)}

    @staticmethod
    def embedded():
        arguments_list = [(todo, ) for todo in TODOS]
        return Embedded('items', Todo, *arguments_list)

    @staticmethod
    def links():
        arguments_list = [('/todos/{}'.format(todo), {'title': todo}) for todo in TODOS]
        return Link('items', *arguments_list)


@pytest.fixture
def app():
    _app = Flask(__name__)
    api = Api(_app)
    api.add_resource(TodoList, '/todos')
    api.add_resource(Todo, '/todos/<todo>')
    return _app


def test_todolist(client):
    response = client.get(url_for('todolist'))
    assert response.status_code == 200
    assert response.json == {'size': 3}


def test_todo(client):
    for todo_key, todo_value in TODOS.items():
        response = client.get(url_for('todo', todo=todo_key))
        assert response.status_code == 200
        assert response.json == todo_value


def test_embedding(client):
    response = client.get(url_for('todolist'), query_string='embed=1')
    assert response.status_code == 200
    assert response.json == {
        'size': 3,
        '_embedded': {
            'items': [{
                'task': 'build an API'
            }, {
                'task': '?????'
            }, {
                'task': 'profit!'
            }]
        }
    }


def test_links(client):
    response = client.get(url_for('todolist'), query_string='links=true')
    assert response.status_code == 200
    assert response.json == {
        'size': 3,
        '_links': {
            'items': [
                {
                    'href': '/todos/todo1',
                    'title': 'todo1'
                }, {
                    'href': '/todos/todo2',
                    'title': 'todo2'
                }, {
                    'href': '/todos/todo3',
                    'title': 'todo3'
                }
            ],
            'self': {
                'href': '/todos'
            }
        },
    }
