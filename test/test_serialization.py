import collections
import io
import unittest

from bandsaw.context import Context
from bandsaw.result import Result
from bandsaw.run import Run
from bandsaw.serialization import SerializableValue, JsonSerializer


class MyCustomException(Exception):
    pass


class MyCustomClass:
    pass


class MySerializableValue(SerializableValue):
    def __init__(self, value):
        self.value = value

    def serialized(self):
        return {'value': self.value}

    @classmethod
    def deserialize(cls, values):
        return MySerializableValue(values['value'])


mytype = collections.namedtuple('mytype', 'a b')


class TestJsonSerializationProvider(unittest.TestCase):

    def setUp(self):
        self.serialization = JsonSerializer()

    def test_serialize_string_value(self):
        stream = io.BytesIO()
        self.serialization.serialize('My string value', stream)
        self.assertEqual(b'"My string value"', stream.getvalue())

    def test_serialize_int_value(self):
        stream = io.BytesIO()
        self.serialization.serialize(1, stream)
        self.assertEqual(b'1', stream.getvalue())

    def test_serialize_float_value(self):
        stream = io.BytesIO()
        self.serialization.serialize(1.0, stream)
        self.assertEqual(b'1.0', stream.getvalue())

    def test_serialize_None_value(self):
        stream = io.BytesIO()
        self.serialization.serialize(None, stream)
        self.assertEqual(b'null', stream.getvalue())

    def test_serialize_True_value(self):
        stream = io.BytesIO()
        self.serialization.serialize(True, stream)
        self.assertEqual(b'true', stream.getvalue())

    def test_serialize_False_value(self):
        stream = io.BytesIO()
        self.serialization.serialize(False, stream)
        self.assertEqual(b'false', stream.getvalue())

    def test_serialize_dict_value(self):
        stream = io.BytesIO()
        self.serialization.serialize({'a': 'value'}, stream)
        self.assertEqual(b'{"a":"value"}', stream.getvalue())

    def test_serialize_list_value(self):
        stream = io.BytesIO()
        self.serialization.serialize(['a', 'value'], stream)
        self.assertEqual(b'["a","value"]', stream.getvalue())

    def test_serialize_tuple(self):
        stream = io.BytesIO()
        self.serialization.serialize(tuple(['a', 'value']), stream)
        stream.seek(0)
        result = self.serialization.deserialize(stream)
        self.assertEqual(tuple, type(result))
        self.assertEqual('a', result[0])
        self.assertEqual('value', result[1])

    def test_serialize_importable_namedtuple(self):
        value = mytype(1, 2)
        stream = io.BytesIO()
        self.serialization.serialize(value, stream)
        stream.seek(0)
        result = self.serialization.deserialize(stream)
        self.assertEqual(mytype, type(result))
        self.assertEqual(1, result[0])
        self.assertEqual(1, result.a)
        self.assertEqual(2, result[1])
        self.assertEqual(2, result.b)

    def test_serialize_dynamic_namedtuple(self):
        myothertype = collections.namedtuple('myothertype', 'a b')
        value = myothertype(1, 2)
        stream = io.BytesIO()
        self.serialization.serialize(value, stream)
        stream.seek(0)
        result = self.serialization.deserialize(stream)
        self.assertEqual(myothertype.__name__, type(result).__name__)
        self.assertEqual(myothertype.__module__, type(result).__module__)
        self.assertEqual(1, result[0])
        self.assertEqual(1, result.a)
        self.assertEqual(2, result[1])
        self.assertEqual(2, result.b)

    def test_serialize_exception(self):
        stream = io.BytesIO()
        self.serialization.serialize(ValueError("An error"), stream)
        stream.seek(0)
        result = self.serialization.deserialize(stream)
        self.assertEqual(ValueError, type(result))
        self.assertEqual('An error', result.args[0])

    def test_serialize_custom_exception(self):
        stream = io.BytesIO()
        self.serialization.serialize(MyCustomException("An error"), stream)
        stream.seek(0)
        result = self.serialization.deserialize(stream)
        self.assertEqual(MyCustomException, type(result))
        self.assertEqual('An error', result.args[0])

    def test_serialize_json_serializable(self):
        stream = io.BytesIO()
        self.serialization.serialize(MySerializableValue('A value'), stream)
        stream.seek(0)
        result = self.serialization.deserialize(stream)
        self.assertEqual(MySerializableValue, type(result))
        self.assertEqual('A value', result.value)

    def test_deserialize_with_unknown_serializer(self):
        stream = io.BytesIO(b'{"_serializer":"UnknownSerializer"}')
        with self.assertRaisesRegex(TypeError, "Unknown serializer 'UnknownSerializer'"):
            self.serialization.deserialize(stream)

    def test_serialize_with_missing_serializer(self):
        stream = io.BytesIO()
        with self.assertRaises(TypeError):
            self.serialization.\
                serialize(MyCustomClass(), stream)

    def test_serialize_context(self):
        context = Context({'my-attribute': 1})
        stream = io.BytesIO()
        self.serialization.serialize(context, stream)
        stream.seek(0)
        deserialized_context = self.serialization.deserialize(stream)
        self.assertEqual(deserialized_context.attributes, {'my-attribute': 1})

    def test_serialize_run(self):
        run = Run('my-id', [1, 2], {'kwarg': 1})
        stream = io.BytesIO()
        self.serialization.serialize(run, stream)
        stream.seek(0)
        deserialized_run = self.serialization.deserialize(stream)
        self.assertEqual(deserialized_run.run_id, run.run_id)
        self.assertEqual(deserialized_run.args, run.args)
        self.assertEqual(deserialized_run.kwargs, run.kwargs)

    def test_serialize_result_with_value(self):
        result = Result(value='My value')
        stream = io.BytesIO()
        self.serialization.serialize(result, stream)
        stream.seek(0)
        deserialized_result = self.serialization.deserialize(stream)
        self.assertEqual(deserialized_result, result)

    def test_serialize_result_with_exception(self):
        result = Result(exception=ValueError('error'))
        stream = io.BytesIO()
        self.serialization.serialize(result, stream)
        stream.seek(0)
        deserialized_result = self.serialization.deserialize(stream)
        self.assertEqual(deserialized_result, result)


if __name__ == '__main__':
    unittest.main()
