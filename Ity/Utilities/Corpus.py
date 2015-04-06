# coding=utf-8
__author__ = 'kohlmannj'

import os
import Ity
from Ity.Utilities.FilePaths import get_files_in_path, get_valid_path


class Corpus(object):

    def __init__(
        self,
        path,
        name=None,
        extensions=(".txt",),
        texts_path=None,
        metadata_path=None,
        output_path=None
    ):
        # Main Corpus Path
        if type(path) is not str:
            raise ValueError("Invalid path argument provided.")
        # If we didn't get an absolute path, assume it's a path relative to Ity.corpus_root.
        if not os.path.isabs(path):
            path = os.path.join(Ity.corpus_root, path)
        # This call to os.path.abspath(), among other things, removes trailing
        # slashes from the path.
        self.path = os.path.abspath(path)
        # Okay, does the path actually exist?
        if not os.path.exists(self.path):
            raise IOError("Corpus at path '%s' does not exist." % self.path)
        # Texts Path
        self.texts_path = get_valid_path(
            path=texts_path,
            relative_path_base=self.path,
            fallback_path=self.path
        )
        # It's NOT okay if this path doesn't exist.
        if type(self.texts_path) is not str or not os.path.exists(self.texts_path):
            raise ValueError("Path to texts ('%s') doesn't exist." % self.texts_path)
        # Corpus Name
        if name is None or type(name) is not str:
            name = os.path.basename(self.path)
        self.name = name
        # Metadata Path
        self.metadata_path = get_valid_path(
            path=metadata_path,
            relative_path_base=self.path,
            fallback_path=os.path.join(Ity.metadata_root, self.name)
        )
        # Output Path
        self.output_path = get_valid_path(
            path=output_path,
            relative_path_base=self.path,
            fallback_path=os.path.join(Ity.output_root, self.name)
        )
        # Extensions
        if extensions is None or type(extensions) is str or len(extensions) == 0:
            raise ValueError("Invalid extensions argument provided.")
        self.extensions = extensions
        self._texts = None
        self.metadata = {}
        self.batch_format_data = {}

    @property
    def texts(self):
        if self._texts is None:
            self._texts = get_files_in_path(self.texts_path, self.extensions)
        return self._texts
