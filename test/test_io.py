import io
import unittest

from bandsaw.io import BytearrayGeneratorToStream, read_stream_to_generator


def generator(count=1, size=1):
    for i in range(count):
        yield b'12345'*size


class TestBytearrayGeneratorToStream(unittest.TestCase):

    def test_empty_generator_leads_to_empty_stream(self):
        stream = BytearrayGeneratorToStream(generator(0))
        result = stream.readall()
        self.assertEqual(b'', result)

    def test_single_item_in_generator_is_copied_to_stream(self):
        stream = BytearrayGeneratorToStream(generator())
        result = stream.readall()
        self.assertEqual(b'12345', result)

    def test_generator_items_are_partially_kept(self):
        stream = BytearrayGeneratorToStream(generator(2200))
        result = stream.readall()
        self.assertEqual(b'12345'*2200, result)

    def test_too_buffer_size_bigger_than_items_joins_items(self):
        stream = BytearrayGeneratorToStream(generator(2, 10))
        buffer = bytearray(100)
        read_bytes = stream.readinto(buffer)
        self.assertEqual(b'12345'*20, buffer)
        self.assertEqual(100, read_bytes)
        read_bytes = stream.readinto(buffer)
        self.assertEqual(0, read_bytes)


class TestReadStreamToGenerator(unittest.TestCase):

    def test_empty_stream_doesnt_yield_anything(self):
        stream = io.BytesIO(b'')
        generator = read_stream_to_generator(stream)
        result = next(generator, None)
        self.assertIsNone(result)

    def test_if_is_splitted_when_size_smaller_than_buffer(self):
        stream = io.BytesIO(b'1'*10)
        generator = read_stream_to_generator(stream, 8)
        result = next(generator)
        self.assertEqual(b'11111111', result)
        result = next(generator)
        self.assertEqual(b'11', result)
        result = next(generator, None)
        self.assertIsNone(result)

    def test_if_single_value_if_buffer_bigger_than_stream_length(self):
        stream = io.BytesIO(b'1'*5)
        generator = read_stream_to_generator(stream, 8)
        result = next(generator)
        self.assertEqual(b'11111', result)
        result = next(generator, None)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
