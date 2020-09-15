import random
import string
import uuid
from hashlib import sha512

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from users_app.fields import EmailField


class User(Model):
    class ROLES:
        REGULAR_USER = 0
        ADMIN = 1

    user_id = columns.UUID(primary_key=True)
    username = columns.Text(required=True, index=True)
    first_name = columns.Text(required=True)
    last_name = columns.Text(required=True)
    email = EmailField(required=True)
    password = columns.Text(required=True)
    created = columns.DateTime()
    updated = columns.DateTime()
    role = columns.Integer(default=ROLES.REGULAR_USER)
    is_active = columns.Boolean(index=True, default=True)
    ban_reason = columns.Text()
    deleted = columns.Boolean(default=False, index=True)

    api_key = columns.Text(index=True)

    def __init__(self, **values):
        super().__init__(**values)
        if not self.user_id:
            self.user_id = self.generate_user_id()
            self.password = self.hash_password(values.pop('password'))

    def check_password(self, password):
        return sha512_crypt.verify(password, self.password)

    def generate_user_id(self):
        return uuid.uuid4().hex

    @staticmethod
    def hash_password(password):
        return sha512_crypt.hash(password)

    @staticmethod
    def generate_api_key(length=32):
        return ''.join(
            random.choice(string.ascii_letters + string.digits) for _ in
            range(length))

    def __repr__(self):
        return "<User(user_id='{}')>".format(self.user_id)
