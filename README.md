# Flask-RESTful-HAL

## Introduction

*Flask-RESTful-HAL* is an extension for [Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/). It adds
support for building [HAL APIs](http://stateless.co/hal_specification.html).

## Installation

The latest version can be obtained from PyPI:

```python
pip install flask-restful-hal
```

## Usage

*Flask-RESTful-HAL* extends the `Resource` base class of Flask-RESTful. Instead of defining a `get` method, a static
`data` method must be implemented which returns the contents of the resource class. In addition the two optional static
methods `embedded` and `links` can be defined to describe which resources are embedded and linked to the current
resource.

### Example of a minimal resource class

```python
from flask import Flask
from flask_restful_hal import Api, Resource

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


app = Flask(__name__)
api = Api(app)
api.add_resource(Todo, '/todos/<todo>')
app.run()
```

In this example, the only required method `data` is implemented and returns the requested todo entry as a Python
dictionary. By default, this dictionary is parsed to a json string and returned in an HTTP response with content type
`application/hal+json`. If the Python package `json2html` is installed, the client can request an HTML output as an
alternative (by sending `Accept: text/html`).

When requesting the resource, the client may add the query string `links=true` to get linked resources. Since no `links`
method is implemented, only the default `self` link will be included in the response.

### Example of a resource class with embedded and linked resources

```python
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
        arguments_list = [(todo, ) for todo in sorted(TODOS.keys())]
        return Embedded('items', Todo, *arguments_list)

    @staticmethod
    def links():
        arguments_list = [('/todos/{}'.format(todo), {'title': todo}) for todo in sorted(TODOS.keys())]
        return Link('items', *arguments_list)


app = Flask(__name__)
api = Api(app)
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<todo>')
app.run()
```

1. Links can be added by returning one or multiple `Link` objects from a static `links` routine. The `Link` constructor
   takes a relationship (e.g. `collection`, `up` or `item`) and one or multiple link targets. Link targets can either be
   expressed as a string (href attribute) or as a tuple consisting of a href string and a dictionary with extra
   attributes. In the example `title` is used as an extra attribute.
2. Embedded resources are expressed with one or multiple `Embedded` objects. Again, the first parameter is a
   relationship. The second parameter is the embedded resource class and the following parameters are tuples with
   constructor arguments for that class.

By default, no resources are embedded. Embedding resources can be requested with the query string `embed=true` which
affects all resources recursively (embedded resources can embed resources as well). This behavior can be changed by
specifying a concrete level of embedding (e.g. `embed=2` would only embed two levels of resources).