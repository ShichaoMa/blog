import numbers
import datetime

from collections import Sequence
from apistellar import validators
from apistellar.types.formats import BaseFormat, DATETIME_REGEX, ValidationError


from ..utils import default_tz

class TsFormat(BaseFormat):

    type = numbers.Number
    default_tz = default_tz
    name = "ts"

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        """
        赋值和format会调用valiate，转普通类型转换成self.type类型
        :param value:
        :return:
        """
        if isinstance(value, (str, bytes)):
            match = DATETIME_REGEX.match(value)
            if match:
                kwargs = {k: int(v) for k, v in
                          match.groupdict().items() if v is not None}
                return datetime.datetime(
                    **kwargs, tzinfo=self.default_tz).timestamp()
        raise ValidationError('Must be a valid timestamp.')

    def to_string(self, value):
        """
        所有最终会调用__getitem__的方法，会调用这个方法来反序列化，__getattr__则不会。
        :param value:
        :return:
        """
        try:
            return datetime.datetime.fromtimestamp(
                value, self.default_tz).strftime("%Y-%m-%d %H:%M:%S")
        except AttributeError:
            return str(value)


class TagsFormat(BaseFormat):

    type = list
    name = "tags"

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        if isinstance(value, str):
            return value.split(",")
        if isinstance(value, bytes):
            return value.decode().split(",")
        if isinstance(value, Sequence):
            return list(value)
        raise ValidationError('Must be a valid tags.')

    def to_string(self, value):
        if isinstance(value, str):
            value = value.split(",")
        return ",".join(value)


class Timestamp(validators.String):

    def __init__(self, **kwargs):
        super().__init__(format='ts', **kwargs)


class Boolean(validators.Validator):
    def validate(self, value, definitions=None, allow_coerce=False):
        if value is None and self.has_default():
            return self.get_default()
        elif value is None and self.allow_null:
            return None
        elif value is None:
            self.error('null')

        elif not isinstance(value, bool):
            return bool(value)

        return value


class Tags(validators.String):
    def __init__(self, **kwargs):
        super().__init__(format='tags', **kwargs)

