import json
from django.db import models

class JSONField(models.Field):
    'Keeps a JSON-serializable object as a text in the database.'

    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection):
        try:
            return json.loads(value)
        except:
            return None

    def to_python(self, value):
        if value is None:
            return None
        return self.from_db_value(value, None, None)

    def get_prep_value(self, value):
        return json.dumps(value)


class LongJSONField(JSONField):
    'Similar to JSONField, but with LONGTEXT type'

    def db_type(self, connection):
        return 'longtext'
