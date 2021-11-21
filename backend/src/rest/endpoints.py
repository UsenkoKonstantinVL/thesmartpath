import traceback
from typing import Tuple

from flask_restful import Resource
from rest.errors import InternalServerError


class ExampleApi(Resource):
    def get(self) -> Tuple[str, int]:
        try:
            return "OK", 200
        except Exception:
            print(traceback.format_exc())
            raise InternalServerError
