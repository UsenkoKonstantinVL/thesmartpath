from werkzeug.exceptions import HTTPException


class InternalServerError(HTTPException):
    pass


class SchemaValidationError(HTTPException):
    pass


class BadRequestError(HTTPException):
    pass


errors = {
    "InternalServerError": {
        "message": "Something went wrong",
        "status": 500
    },
    "SchemaValidationError": {
        "message": "Request is missing required fields or providing unexpected fields",
        "status": 400
    },
    "BadRequestError": {
        "message": "Request is providing unacceptable values for some fields",
        "status": 400
    },

}
