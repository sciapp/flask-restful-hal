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

*Flask-RESTful-HAL* extends the `Resource` base class of Flask-RESTful. Instead of defining a `get` method, a `data`
method must be implemented which returns the contents of the resource class. In addition the two optional methods
`embedded` and `links` can be defined to describe which resources are embedded and linked to the current resource. All
three methods can be defined as `staticmethod` if no data needs to be shared between the method invocations (see the
[section about data sharing](#sharing-data-between-methods) for more information).

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
from flask import Flask
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

### Sharing data between methods

In most cases, the `data`, `embedded` and `links` methods need access to the same data source. In order to avoid
accessing the data backend (for example a database) three times with similar queries you can define a forth `pre_hal`
method which is called on every `GET` request before `data`, `embedded` or `links` are executed. In `pre_hal` you can
access the data backend and cache the result in instance variables of the current resource object.

```python
class TodoList(Resource):
    def pre_hal(self, embed, include_links, todo):
        self.todos = db.query(...)

    def data(self):
        return {'size': len(self.todos)}

    def embedded(self):
        arguments_list = [(todo, ) for todo in sorted(self.todos.keys())]
        return Embedded('items', Todo, *arguments_list)

    def links(self):
        arguments_list = [('/todos/{}'.format(todo), {'title': todo}) for todo in sorted(self.todos.keys())]
        return Link('items', *arguments_list)
```

### Securing API endpoints

*Flask-RESTful-HAL* does not include any authorization mechanisms to secure your api endpoints. However, you can easily
integrate available Flask extensions by overriding the `Resource` class. The following example uses
[Flask-JWT-Extended](http://flask-jwt-extended.readthedocs.io/en/latest/) to secure `GET` requests with *JSON Web
Tokens*. Tokens are generated by a special endpoint `/auth_token` that is secured with *basic auth*:

```python
from flask import Flask, g
from flask_httpauth import HTTPBasicAuth
from flask_jwt_extended import create_access_token, jwt_required
from flask_restful import Resource as RestResource
from flask_restful_hal import Api, Embedded, Link, Resource as HalResource

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

http_basic_auth = HTTPBasicAuth()


@http_basic_auth.verify_password
def verify_password(username, password):
    g.username = username
    # TODO: implement some check here...
    return True


class SecuredHalResource(HalResource):
    @jwt_required
    def get(self, **kwargs):
        return super().get(**kwargs)


class AuthToken(RestResource):
    @http_basic_auth.login_required
    def get(self):
        auth_token = create_access_token(identity=g.username)
        return jsonify({'auth_token': auth_token})


class Todo(SecuredHalResource):
    @staticmethod
    def data(todo):
        return TODOS[todo]


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'use your super secret key here!'
api = Api(app)
api.add_resource(AuthToken, '/auth_token')
api.add_resource(Todo, '/todos/<todo>')
app.run()
```

Tokens requested with the `/auth_token` endpoint can then be used in the HTTP authorization header with the *Bearer*
scheme to gain access to secured resources:

```http
Authorization: Bearer <token>
```
