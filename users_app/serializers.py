import re

from marshmallow import Schema, fields


def email_validator(value):
    EMAIL_REGEX = re.compile(
        r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    if not EMAIL_REGEX.match(value):
        return False
    return True


class UserSchema(Schema):
    user_id = fields.UUID(dump_only=True)
    username = fields.Str(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    email = fields.Str(required=True, validate=email_validator)
    password = fields.Str(load_only=True)
    role = fields.Integer(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created = fields.DateTime()
    updated = fields.DateTime()
