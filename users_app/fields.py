import re

from cassandra.cqlengine import ValidationError, columns


class EmailField(columns.Text):
    EMAIL_REGEX = re.compile(
        r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    def validate(self, value):
        super().validate(value)
        if not self.EMAIL_REGEX.match(value):
            raise ValidationError(
                '{} is not valid email address'.format(value)
            )
        return value
