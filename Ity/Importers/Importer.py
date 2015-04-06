# coding=utf-8
__author__ = 'kohlmannj'

import abc
import os
from Ity import metadata_root


class Importer(object):
    __metaclass__ = abc.ABCMeta

    @classmethod
    @abc.abstractmethod
    def get_export_path(cls):
        """
        Returns a string representing the path to the file or folder of files
        this Importer creates after importing metadata. This merely a path;
        no further validation is performed.

        """
        pass

    # def __init__(self, overwrite=True):
    #     self.overwrite = overwrite
    #     # Get the export path. This could be a file or folder, depending on how
    #     # the author of a subclass decides it needs to work.
    #     self.export_path = __name__.get_export_path()
    #     # See if the export is valid.
    #     if os.path.exists(self.export_path):
    #         if not self.overwrite:
    #             raise ValueError("Export path already exists (and we were told not to overwrite).")
    #     # Some common importing operations might go here.
