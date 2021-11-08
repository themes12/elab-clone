import json

from django.db import models
from commons.models import TestCaseResult

class AnswerField(models.Field):
    """
    AnswerField keeps answer dict as jsoned string.

    >>> a = AnswerField()
    >>> a.get_prep_value({0:'hello',1:'world'})
    '{"0": "hello", "1": "world"}'

    >>> a.from_db_value('{"0": "hello", "1": "world"}')
    {0: 'hello', 1: 'world'}
    """

    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection):
        if value==None or value=='':
            return {}
        else:
            try:
                strkeyed_answer = json.loads(str(value))
                # have to convert keys from str to int, because json dumps
                # dict that uses str as keys
                answer = {}
                for k,v in strkeyed_answer.items():
                    answer[int(k)]=v
                return answer
            except ValueError:
                return {}

    def to_python(self, value):
        if isinstance(value, dict):
            return value
        return self.from_db_value(value,None,None)

    def get_prep_value(self, value):
        return json.dumps(value)


class GradingResultField(models.Field):
    """
    GradingResultField keeps a list of test results, each of which is an
    instance of TestCase Result.
    """

    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return []
        return [ TestCaseResult.create_from_db(int(r)) 
                 for r in value.split(',') ]

    def to_python(self, value):
        if isinstance(value, list):
            return value
        return self.from_db_value(value)

    def get_prep_value(self, value):
        return ','.join([str(r.to_db()) for r in value])
