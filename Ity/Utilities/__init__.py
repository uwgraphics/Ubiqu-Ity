# coding=utf-8
__author__ = 'kohlmannj'

import os
import Ity
import FilePaths
from Corpus import Corpus
from CorpusText import CorpusText

__all__ = ["Corpus", "CorpusText", "FilePaths"]

def get_models(metadata_root_path=None):
    if metadata_root_path is None:
        metadata_root_path = Ity.metadata_root
    return os.listdir(metadata_root_path)

def get_corpora(root_path=None, metadata_root_path=None):
    """
    Returns a list of corpus_names (strs) which are available for use with Ity.
    A corpus is available if, for a folder existing in Ity.corpus_root, a
    folder of the same name in Ity.metadata_root also exists. Why yes, this is
    an incredibly naïve check!

    :return:
    """
    check_for_individual_corpora_metadata = True
    if root_path is None:
        root_path = Ity.corpus_root
    if metadata_root_path is None:
        metadata_root_path = Ity.metadata_root
    else:
        check_for_individual_corpora_metadata = False
    available_corpora = {}
    # Return the empty dict if the root path is outside Ity.corpus_root.
    common_corpora_prefix = os.path.commonprefix([
        root_path, Ity.corpus_root
    ])
    common_metadata_prefix = os.path.commonprefix([
        metadata_root_path, Ity.metadata_root
    ])
    if (
        common_corpora_prefix != Ity.corpus_root or
        common_metadata_prefix != Ity.metadata_root
    ):
        return available_corpora
    for corpus_name in os.listdir(root_path):
        corpus_path = os.path.join(root_path, corpus_name)
        # Only include the corpus if we have its corpus folder and metadata
        # folder.
        if check_for_individual_corpora_metadata:
            corpus_metadata_path = os.path.join(metadata_root_path, corpus_name)
        else:
            corpus_metadata_path = metadata_root_path
        if (
            corpus_name not in available_corpora and
            os.path.exists(corpus_path) and
            os.path.isdir(corpus_path) and
            os.path.exists(corpus_metadata_path) and
            os.path.isdir(corpus_metadata_path)
        ):
            # Get the files in this corpus.
            corpus_data = dict(
                texts=[],
                corpora=get_corpora(
                    root_path=corpus_path,
                    metadata_root_path=os.path.join(
                        Ity.metadata_root,
                        corpus_name
                    )
                )
            )
            # Populate corpus_data["texts"]
            for file_name in os.listdir(corpus_path):
                file_path = os.path.join(
                    corpus_path,
                    file_name
                )
                if not os.path.exists(file_path):
                    continue
                elif os.path.isfile(file_path):
                    corpus_data["texts"].append(
                        os.path.splitext(file_name)[0]
                    )
            available_corpora[corpus_name] = corpus_data
    return available_corpora

