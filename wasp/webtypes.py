import json
from collections import defaultdict
from urllib import parse
from .router import Methods


class QueryParams:
    """
    A dictionary that stores multiple values per key.

    this has all the normal dictionary methods, and works as normal but does
    not override a key when `add` is used, and also has `getall`
    """
    __slots__ = ['mappings']

    def __init__(self):
        self.mappings = defaultdict(list)

    def get(self, name, default=None):
        return self.mappings.get(name, [default])[0]

    def getall(self, name, default=None):
        return self.mappings.get(name, default)

    def __getitem__(self, key):
        try:
            return self.mappings.__getitem__(key)[0]
        except IndexError:
            raise KeyError('Invalid Key: {key}'.format(key))

    def __setitem__(self, key, value):
        raise TypeError('MultiDict does not support item assignment. '
                        'Use .add(k, v) instead.')

    def add(self, name, value):
        self.mappings[name].append(value)


class Request:
    def __init__(self, headers: dict = None,
                 path: str = None, correlation_id: str = None,
                 method: str = None, query_string: str = None,
                 body: bytes=None, host: str = None):

        if not headers:
            headers = dict()

        self.headers = headers
        self.path = path
        self.correlation_id = correlation_id
        self.method = Methods(method.upper())
        self.query_string = query_string
        self._query_params = None
        self.body = body
        self.host = host
        self.path_params = {}
        self._handler = None

    def cookies(self) -> dict:
        # a dictionary of cookies
        return dict()

    @property
    def query(self) -> QueryParams:
        # parse query string into a dictionary
        if not self._query_params:
            self._query_params = QueryParams()
            qs = parse.parse_qsl(self.query_string)
            for k, v in qs:
                self._query_params.add(k, v)
        return self._query_params

    def json(self) -> dict:
        # convert body into a json dict
        return json.loads(self.body.decode())

    def get_path_var(self, key, default=None):
        return self.path_params.get(key, default=default)

    def __str__(self):
        query = '?' + self.query_string if self.query_string else ''
        return('<Request({method} {path}{query})@{id}>'
               .format(method=self.method, path=self.path,
                       query=query , id=id(self)))


class Response:
    def __init__(self, headers=None, correlation_id=None,
                 body=None, status=200):
        if not headers:
            headers = dict()
        self.headers = headers
        self.correlation_id = correlation_id
        self.body = body
        self.status = status
        self._data = None

    def __str__(self):
        return('<Response({status})@{id}>'
               .format(status=self.status, id=id(self)))

    @property
    def data(self):
        if self._data is None and self.body:
            self._data = json.dumps(self.body).encode()
        return self._data

    @property
    def reason(self):
        # reason portion of status code
        # for example, the reason in HTTP 200 OK is "OK"
        return 'OK'


class ResponseError(Exception):
    def __init__(self, status, *, body=None, headers=None,
                 correlation_id=None):
        super().__init__()
        self.response = Response(status=status, body=body, headers=headers,
                                 correlation_id=correlation_id)
