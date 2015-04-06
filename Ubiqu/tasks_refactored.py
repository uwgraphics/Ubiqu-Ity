# coding=utf-8
from __future__ import absolute_import

from collections import OrderedDict
import codecs
import json
import os
import sys
sys.path.append(os.path.join(
    os.path.dirname(os.path.basename(__file__)),
    ".."
))
sys.path.append(os.path.dirname(os.path.basename(__file__)))
import Ity
from Ity.Utilities import Corpus
from Ity.TaskSupport import *
# from celery import Celery, Task
# from celery.utils.log import get_task_logger
#
# celery = Celery(__name__)
# celery.config_from_object("celery_config")
# logger = get_task_logger(__name__)


def upload_corpus(data):
    pass


def process_corpus(
    tokenizer="RegexTokenizer",
    taggers=("DocuscopeTagger",),
    formatters=("HTMLFormatter",),
    batch_formatters=("CSVFormatter",),
    compress_output=False,
    **corpus_options
):
    # if "output_path" in corpus_options:
    #     corpus_options["output_path"] = os.path.join(
    #         celery.conf["TMP_ROOT"]
    #     )5
    corpus = Corpus(**corpus_options)
    corpus.tokenizer = init_tokenizer(tokenizer)
    corpus.taggers = [
        init_tagger(tagger)  # , corpus=corpus)
        for tagger in taggers
    ]
    corpus.formatters = [
        init_formatter(formatter)  # , corpus=corpus)
        for formatter in formatters
    ]
    corpus.batch_formatters = [
        init_formatter(batch_formatter)  # , corpus=corpus)
        for batch_formatter in batch_formatters
    ]
    results = OrderedDict()
    for name, path in corpus.get_texts().items():
        results[name] = process_text(
            path=path,
            tokenizer=corpus.tokenizer,
            taggers=corpus.taggers,
            formatters=corpus.formatters,
            corpus=corpus
        )
    return corpus, results


def save_corpus(corpus, results, save_keys=("formats",)):
    saved_files = {}
    # Make sure the corpus output path exists.
    if not os.path.exists(corpus.output_path):
        os.makedirs(corpus.output_path)
    for result in results.values():
        result_folder_path = os.path.join(
            corpus.output_path,
            result["name"]
        )
        if not os.path.exists(result_folder_path):
            os.makedirs(result_folder_path)
        for key in save_keys:
            if key not in result:
                continue
            if key not in saved_files:
                saved_files[key] = OrderedDict()
            key_file_name = result["name"] + "_" + key
            key_content = result[key]
            if type(key_content) is str:
                key_file_name += ".txt"
            else:
                key_content = json.dumps(key_content)
                key_file_name += ".json"
            key_file_path = os.path.join(
                result_folder_path,
                key_file_name
            )
            with codecs.open(key_file_path, "w", encoding="utf-8") as key_file:
                key_file.write(key_content)
            saved_files[key][key_file_name] = key_file_path
    return saved_files


def process_text(
    path,
    name=None,
    tokenizer="RegexTokenizer",
    taggers=("DocuscopeTagger",),
    formatters=("HTMLFormatter",),
    corpus=None,
    output_path=None,
    **module_init_options
):
    """
    Given a path to a text file, process a text using Ity.
    """
    text = get_text(path)
    tokens = []
    tags = {}
    formats = {}
    if type(name) is not str:
        name = os.path.splitext(
            os.path.basename(path)
        )[0]
    tokenizer_init_options = {}
    if type(tokenizer) is str and tokenizer in module_init_options:
        tokenizer_init_options = module_init_options[tokenizer]
    tokens = tokenize_text(text, tokenizer, **tokenizer_init_options)
    for tagger in taggers:
        tagger_init_options = {}
        if type(tagger) is str and tagger in module_init_options:
            tagger_init_options = module_init_options[tagger]
        tag_names, tag_maps = tag_tokens(tokens, tagger, corpus=corpus, **tagger_init_options)
        tags[tagger] = {
            "tags": tag_names,
            "tags": tag_maps
        }
    for formatter in formatters:
        formatter_init_options = {}
        if type(formatter) is str and formatter in module_init_options:
            formatter_init_options = module_init_options[formatter]
        formats[formatter] = format_text(
            tags,
            tokens,
            text,
            formatter,
            corpus,
            **formatter_init_options
        )
    return dict(
        path=path,
        name=name,
        text=text,
        tokens=tokens,
        tags=tags,
        formats=formats
    )


def get_text(text_path):
    with codecs.open(text_path, "r", encoding="utf-8") as text_file:
        text = text_file.read()
    return text


def tokenize_text(text, tokenizer="RegexTokenizer", **init_options):
    """
    Tokenizes a text string.
    :param text_path: The file path to the text file (str)
    :param tokenizer: The name of the Ity.Tokenizers module to use (str)
    :param tokenizer_options: Additional options to instantiate the Tokenizer
    :return:
    """
    try:
        tokenizer_instance = init_tokenizer(tokenizer, **init_options)
    except (ValueError, ImportError):
        raise ValueError("Invalid tokenizer module specified.")
    tokens = tokenizer_instance.tokenize(text)
    return tokens


def tag_tokens(tokens, tagger="DocuscopeTagger", corpus=None, **init_options):
    """
    Tags a tuple of tokens.
    :param text_path: The file path to the text file (str)
    :param tokenizer: The name of the Ity.Tokenizers module to use (str)
    :param tokenizer_options: Additional options to instantiate the Tokenizer
    :return:
    """
    try:
        tagger_instance = init_tagger(tagger, **init_options)
    except (ValueError, ImportError):
        raise ValueError("Invalid tagger module specified.")
    tags, tag_maps = tagger_instance.tag(tokens)
    return tags, tag_maps


def format_text(
    tags=None,
    tokens=None,
    text=None,
    formatter="HTMLFormatter",
    corpus=None,
    **init_options
):
    try:
        formatter_instance = init_formatter(formatter, **init_options)
    except (ValueError, ImportError):
        raise ValueError("Invalid tagger module specified.")
    if len(tags.keys()) > 1:
        raise NotImplementedError("Formatters do not support multiple taggers yet.")
    format = formatter_instance.format(tags.values()[0], tokens, text)
    return format


if __name__ == "__main__":
    process_text(text_name="Foobar")
