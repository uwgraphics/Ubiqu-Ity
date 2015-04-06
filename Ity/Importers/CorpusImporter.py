# coding=utf-8
__author__ = 'kohlmannj'

import abc
import os
from Ity import metadata_root


class CorpusImporter(object):
    """
    Imports data for a corpus.

    """
    __metaclass__ = abc.ABCMeta

    @classmethod
    @abc.abstractmethod
    def get_metadata_path(cls, options):
        """
        Returns a string representing the absolute file path to the file or
        folder this Importer creates when it saves its imported metadata to
        disk. This merely a file path; no further validation is performed.

        It's separated as a class method to allow other modules to check
        if a file or folder is associated with a particular Importer or Courier
        module by dint of the fact that a particular file path matches the
        file path at which the Importer would have created its export data.

        The code below, as an example, returns the absolute file path to a
        [model_path].imported file that would be created in metadata_root.

        """
        if "model_path" in options:
            return os.path.join(metadata_root, options["model_path"] + ".imported")

    @classmethod
    @abc.abstractmethod
    def query(cls, corpus_name, options):
        pass

    def __init__(self, corpus_name, overwrite=True):
        self.overwrite = overwrite
        self.metadata_path = __name__.get_metadata_path(corpus_name)
