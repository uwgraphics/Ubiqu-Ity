# coding=utf-8
__author__ = 'kohlmannj'

import os
from collections import OrderedDict

def list_corpus_data_files (
        self,
        corpus_path,
        exts=("txt",)
    ):
        super(CorpusFileSystemImporter, self).__init__(corpus_path)
        # Correct for trailing slash in the corpus path.
        if type(corpus_path) is str and (corpus_path.endswith("/") or corpus_path.endswith("\\")):
            corpus_path = corpus_path[:-1]
        if exts is None or type(exts) is str:
            raise ValueError("Invalid exts argument provided.")
        data = OrderedDict()
        for root, dirnames, filenames in os.walk(self.corpus_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_basename, file_ext = os.path.splitext(filename)[1]
                if file_ext in exts:
                    if file_basename in self.data.keys():
                        raise IOError("Attempting to add the same file to the data list a second time!")
                    data[file_basename] = file_path
        return data
