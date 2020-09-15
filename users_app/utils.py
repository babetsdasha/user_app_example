import json
from decimal import Decimal

from functools import partial


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode()

        return super().default(obj)


class APIException(Exception):
    def __init__(self, message, code='1'):
        super(APIException, self).__init__(self)
        self.message = message
        self.code = code


dumps = partial(json.dumps, cls=JSONEncoder)
