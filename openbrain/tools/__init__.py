import contextlib
import importlib
import inspect
import sys

from openbrain.tools.toolbox import Toolbox
import pkgutil


def register_obtool_classes():
    """Register all OBTool classes in the openbrain.tools package. This makes them available to the Toolbox. No need to manually register them."""
    # Get the current module (assuming __init__.py is in the same directory as your classes)
    current_module = sys.modules[__name__]
    # Dynamically import all submodules
    submodules = import_submodules(current_module.__package__)
    for submodule in submodules.values():
        for obj in inspect.getmembers(submodule):  # inspect.getmembers(submodule))
            # Broken down for troubleshooting
            with contextlib.suppress(KeyError, TypeError):
                identified_class = obj[1]
                Toolbox.register_available_obtool(identified_class)


def import_submodules(package_name):
    """Import all submodules of a module, recursively"""
    package = sys.modules[package_name]
    return {
        name: importlib.import_module(package_name + "." + name)
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__)
    }


register_obtool_classes()
