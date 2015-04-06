# coding=utf-8
__author__ = 'kohlmannj'

import codecs
import os
import Ity
from Ity.Utilities.FilePaths import get_valid_path


class CorpusText(object):

    def __init__(
        self,
        path,
        name=None,
        corpus=None,
        output_path=None
    ):
        # Text Path
        if type(path) is not str:
            raise ValueError("Invalid path argument provided.")
        # Is the path absolute?
        if not os.path.isabs(path):
            # No? Can we figure out where it is based on the corpus argument?
            if (
                corpus is None and
                hasattr(corpus, "texts_path") and
                type(corpus.texts_path) is str
            ):
                path = os.path.join(
                    corpus.texts_path,
                    path
                )
            else:
                raise ValueError("Given a relative path to a text without a corpus argument.")
        # This call to os.path.abspath(), among other things, removes trailing
        # slashes from the path.
        self.path = os.path.abspath(path)
        # Okay, does the path actually exist?
        if not os.path.exists(self.path):
            raise ValueError("Text file at path '%s' does not exist." % self.path)
        # Text Name
        if name is None or type(name) is not str:
            name = os.path.splitext(os.path.basename(self.path))[0]
        self.name = name
        # Text Corpus (may be None)
        self.corpus = corpus
        # Output Path
        self.output_path = get_valid_path(
            path=output_path,
            fallback_path=os.path.join(Ity.output_root, self.name)
        )
        self.metadata = None
        self._text_str = None
        self.tokens = []
        self.tag_data = {}
        self.format_data = {}

    @property
    def text_str(self):
        if self._text_str is None:
            with codecs.open(self.path, "r", encoding="utf-8") as text_file:
                self._text_str = text_file.read()
        return self._text_str
