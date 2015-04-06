# coding=utf-8
__author__ = 'kohlmannj'

import os
from Ity import corpus_root, metadata_root, Importers


class CorpusCourier(object):

    def __init__(self, name):
        self.name = name
        # Do we have a folder in the corpus_root who name matches model_path?
        if self.name not in os.listdir(corpus_root):
            # Change model_path to lowercase, just for kicks.
            # If it's still not in there, raise a ValueError.
            if self.name.lower() not in os.listdir(corpus_root):
                raise ValueError("Corpus named \"%s\" does not exist." % self.name)
        # So the corpus directory exists...good news. Let's get some information about it.
        self.path = os.path.join(corpus_root, self.name)
        # Do we have any metadata for this corpus?
        self.metadata = []
        # If we did have metadata, it'd be in here.
        self.metadata_path = os.path.join(metadata_root, self.name)
        # Check for metadata.
        self._validate_metadata()

    def _validate_metadata(self):
        # If we don't have a metadata path, we have nothing to do.
        if not os.path.exists(self.metadata_path):
            self.metadata_path = None
            return
        # Get the expected metadata paths for all available Importers.
        expected_paths = Importers.get_metadata_paths_for_all_modules({
            "model_path": self.name
        })
        # If we have actual metadata paths that match the expected paths,
        # note that we have that type of metadata for this corpus.
        for path in os.listdir(self.metadata_path):
            full_path = os.path.join(path, self.metadata_path)
            if full_path in expected_paths.keys():
                self.metadata = expected_paths[full_path]

    def query(self, metadata_name, options):
        # We can't do a query if we have no metadata of the requested type.
        if metadata_name not in self.metadata:
            raise ValueError("No \"%s\" metadata available for this corpus." % metadata_name)
        # Okay, we have this metadata type, neat! Do we have a query method for it?
        query_method = getattr(Importers.get_module_by_name(metadata_name), "query")
        if query_method is not None:
            return query_method(options)
        else:
            return None
