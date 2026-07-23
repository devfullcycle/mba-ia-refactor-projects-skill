from errors import ValidationError
from schemas.validators import SchemaValidationError


def validate(validator, payload):
    try:
        return validator(payload)
    except SchemaValidationError as error:
        raise ValidationError(error.message) from error
