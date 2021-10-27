import importlib
import inspect
import os
from pathlib import Path

import pluggy

CHECK_SUM_PROJECT = "check_sum_url"

CHECK_SUM_SPEC = pluggy.HookspecMarker(CHECK_SUM_PROJECT)
CHECK_SUM_IMPL = pluggy.HookimplMarker(CHECK_SUM_PROJECT)


def get_script_directory():
    return os.path.dirname(os.path.realpath(__file__))


def load_plugins():

    result = []

    plugins_dir = Path(get_script_directory()) / Path('checksum_plugins')

    importlib.import_module('checksum_plugins')
    for file_name in plugins_dir.iterdir():

        if file_name.suffix == '.py' and file_name.name.endswith('_plugin.py'):
            module_name = 'checksum_plugins.' + file_name.name[0:-len('.py')]
            result.append(importlib.import_module(module_name))

    return result


def find_factory_classes(modules):

    result = []
    for module in modules:
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if name.endswith('Factory'):
                result.append(cls)
    return result


def load_and_register_factory_classes():
    modules = load_plugins()
    factories = find_factory_classes(modules)

    for factory in factories:
        instance = factory()
        pm.register(instance)


class BaseChecksumHookspecs:

    @CHECK_SUM_SPEC
    def get_plugin_name(self, plugin_class):
        """get the name of the navigator
        """


class NavigatorChecksumHookspecs(BaseChecksumHookspecs):

    @CHECK_SUM_SPEC
    def create_navigator(self, name, target_browser, target_args=None):
        """create a new navigator
        """


class OutputChecksumHookspecs(BaseChecksumHookspecs):
    @CHECK_SUM_SPEC
    def create_output(self, name, target_args=None, additional_args=None):
        """create an output
        """


pm = pluggy.PluginManager(CHECK_SUM_PROJECT)


def get_plugin_name(self, plugin_class):
    if self.CLASS == plugin_class:
        return self.NAME


def create_navigator(self, name):
    if name.lower() == self.NAME and self.CLASS == 'navigator':
        return self.obj


def create_output(self, name):
    if name.lower() == self.NAME and self.CLASS == 'output':
        return self.obj


def register_navigator():
    def f(obj):
        if not hasattr(obj, 'NAME'):
            raise Exception('Error: a plugin requires a class variable NAME')
        factory_name = f'{obj.__name__}Factory'
        factory = type(factory_name,
                       (),
                       {'NAME': obj.NAME,
                        'CLASS': 'navigator',
                        'get_plugin_name': CHECK_SUM_IMPL(get_plugin_name),
                        'create_navigator': CHECK_SUM_IMPL(create_navigator),
                        'obj': obj
                        })

        factory_object = factory()
        pm.register(factory_object)

        return obj

    return f


def register_output():
    def f(obj):
        if not hasattr(obj, 'NAME'):
            raise Exception('Error: a plugin requires a class variable NAME')
        factory_name = f'{obj.__name__}Factory'
        factory = type(factory_name,
                       (),
                       {'NAME': obj.NAME,
                        'CLASS': 'output',
                        'get_plugin_name': CHECK_SUM_IMPL(get_plugin_name),
                        'create_output': CHECK_SUM_IMPL(create_output),
                        'obj': obj
                        })

        factory_object = factory()
        pm.register(factory_object)

        return obj

    return f


def list_navigators():
    return ', '.join(pm.hook.get_plugin_name(plugin_class = 'navigator'))


def list_outputs():
    return ', '.join(pm.hook.get_plugin_name(plugin_class  ='output'))


def get_navigator(name=None, target_browser=None, target_args=None):
    return pm.hook.create_navigator(name=name, target_browser=target_browser, target_args=target_args)


def get_output(name=None, target_args=None):
    return pm.hook.create_output(name=name, target_args=target_args)[0](target_args=target_args)
