import inspect
import sys
import unittest


from bandsaw.modules import object_as_import, import_object, \
    get_loaded_module_name_by_path, _guess_module_name_by_path


def my_fake_main_function():
    pass


class TestObjectAsImport(unittest.TestCase):

    def test_class_defined_in_module(self):
        obj_name, mod_name = object_as_import(TestObjectAsImport)
        self.assertEqual(obj_name, 'TestObjectAsImport')
        self.assertEqual(mod_name, 'test_modules')

    def test_local_function_cant_be_imported(self):
        def my_local_function():
            pass

        with self.assertRaisesRegex(ValueError, "Can't import local"):
            object_as_import(my_local_function)

    def test_objects_from___main____are_mapped(self):
        setattr(my_fake_main_function, '__module__', '__main__')
        self.assertEqual(my_fake_main_function.__module__, '__main__')

        obj_name, mod_name = object_as_import(my_fake_main_function)

        self.assertEqual(obj_name, 'my_fake_main_function')
        self.assertNotEqual(mod_name, '__main__')


class TestImportObject(unittest.TestCase):

    def test_class_defined_in_module(self):
        obj = import_object('TestImportObject', 'test_modules')
        self.assertIs(obj, TestImportObject)

    def test_unknown_object_in_existing_module(self):
        with self.assertRaisesRegex(AttributeError, "has no attribute"):
            import_object('NotExistingName', 'test_modules')

    def test_unknown_module(self):
        with self.assertRaisesRegex(ModuleNotFoundError, "No module named"):
            import_object('NotExistingName', 'non_existing_module')


class TestGetLoadedModuleNameByPath(unittest.TestCase):

    def test_file_is_top_level_module(self):
        module_name = get_loaded_module_name_by_path(__file__)
        self.assertEqual('test_modules', module_name)

    def test_file_is_not_loaded_as_module(self):
        module_name = get_loaded_module_name_by_path(__file__+'.ext')
        self.assertIsNone(module_name)


class TestDetermineModuleFromPath(unittest.TestCase):

    def test_file_is_top_level_module(self):
        module_name = _guess_module_name_by_path(
            '/my/package/module.py',
            ['/my/package'],
        )
        self.assertEqual('module', module_name)

    def test_file_without_py_extension(self):
        with self.assertRaisesRegex(ValueError, "Invalid python module"):
            _guess_module_name_by_path('/my/package/module.ext', [])

    def test_file_is_top_level_module_in_second_path(self):
        module_name = _guess_module_name_by_path(
            '/my/other/module.py',
            ['/my/package', '/my/other'],
        )
        self.assertEqual('module', module_name)

    def test_file_is_outside_of_paths(self):
        module_name = _guess_module_name_by_path(
            '/my/different/module.py',
            ['/my/package', '/my/other'],
        )
        self.assertEqual(None, module_name)

    def test_file_is_second_level(self):
        module_name = _guess_module_name_by_path(
            '/my/other/package/module.py',
            ['/my/package', '/my/other'],
        )
        self.assertEqual('package.module', module_name)


if __name__ == '__main__':
    unittest.main()
