# coding=utf-8
__author__ = 'kohlmannj'

import importlib
import CorpusImporter

__all__ = [
    "CorpusImporter"
]


def get_metadata_paths_for_all_modules(options):
    paths_to_modules = {}
    for module_name in __all__:
        path = get_metadata_path_for_module(module_name, options)
        if path not in paths_to_modules:
            paths_to_modules[path] = module_name
        # Yikes, some other module is expecting to have generated metadata at
        # the same exact file path as this module! Not good.
        else:
            raise StandardError(
                "Internal error: metadata path conflict between %s module and %s module." % (
                    module_name,
                    paths_to_modules[path]
                )
            )


def get_module_by_name(module_name):
    return importlib.import_module(module_name, package="Ity.Importers")


def get_metadata_path_for_module(module_name, options=None):
    get_metadata_path_method = get_module_by_name(module_name).get_metadata_path
    return get_metadata_path_method(options)
