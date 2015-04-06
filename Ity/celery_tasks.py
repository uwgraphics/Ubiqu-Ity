# coding=utf-8
from __future__ import absolute_import
import os
import sys
sys.path.append(os.path.join(
    os.path.dirname(os.path.basename(__file__)),
    ".."
))
sys.path.append(os.path.dirname(__file__))


from collections import OrderedDict
import codecs
import json
import hashlib


# Ity Imports
import Ity
from Ity.Utilities import Corpus, CorpusText
from Ity.TaskSupport import *


# Celery
from celery import Celery
from celery.utils.log import get_task_logger
celery = Celery(__name__)
celery.config_from_object("celery_config")
logger = get_task_logger(__name__)


# Sentry / Raven
if "SENTRY_DSN" in celery.conf:
    from raven import Client
    from raven.contrib.celery import register_signal
    client = Client(
        dsn=celery.conf["SENTRY_DSN"]
    )
    register_signal(client)


@celery.task
def upload_corpus(data):
    pass


@celery.task
def process_corpus(
    tokenizer="RegexTokenizer",
    taggers=("DocuscopeTagger",),
    formatters=("HTMLFormatter",),
    corpus_formatters=("CSVFormatter",),
    **corpus_kwargs
):
    """
    Processes an entire corpus of texts, given a path to them, using a certain
    tokenizer, taggers, formatters, and corpus formatters.

    Additional arguments include "path", "output_path" and more---
    please refer to init method of the Ity.Utilities.Corpus class.

    By the way, while the `formatters` operate on single texts with their
    format() method, `corpus_formatters` operate on the entire corpus with
    their batch_format() method. That's the distinction.

    The `tokenizer` argument, as well as **any tuple item** in the `taggers`,
    `formatters`, or `corpus_formatters` arguments may be one of the following:

    * A **str** equal to the name of an appropriate Ity class, i.e.
      `tokenizer="RegexTokenizer"`, `taggers=("DocuscopeTagger", "CSVTagger")`
    * An appropriate **class** that has been imported, i.e.
      `tokenizer=RegexTokenizer`, `taggers=(DocuscopeTagger, CSVTagger)`
    * An **instance** of an appropriate Ity class, i.e.
      `tokenizer=my_tokenizer`, `taggers=(first_tagger, second_tagger)`

    You may process texts in a corpus with multiple taggers and formatters,
    but may only use one tokenizer; the rest of the modules up the chain have
    to agree on *something*, right?

    :param tokenizer: A str, an Ity Tokenizer class,
                      or an Ity Tokenizer instance.
    :param taggers: A tuple of strs, Ity Tagger classes,
                    or Ity Taggers instances.
    :param formatters: A tuple of strs, Ity Formatter classes,
                       or Ity Formatter instances.
    :param corpus_formatters: A tuple of strs, Ity Formatter classes,
                              or Ity Formatter instances.
    :param corpus_kwargs: Keyword arguments to be passed to the
                          Ity.Utilities.Corpus init() method:
                          `path`, `output_path`, etc.
    :return:
    """
    corpus = Corpus(**corpus_kwargs)
    # Take the tokenizer, taggers, formatters, and batch_formatters arguments
    # and initialize whatever modules we need.
    tokenizer = init_tokenizer(tokenizer)
    taggers = [
        init_tagger(tagger)
        for tagger in taggers
    ]
    formatters = [
        init_formatter(formatter)
        for formatter in formatters
    ]
    corpus_formatters = [
        init_formatter(corpus_formatter)
        for corpus_formatter in corpus_formatters
    ]
    # Process each text in the corpus.
    results = OrderedDict()
    for name, path in corpus.texts.items():
        results[name] = process_text(
            path=path,
            tokenizer=tokenizer,
            taggers=taggers,
            formatters=formatters,
            corpus_instance=corpus
        )
    # Use some of the results to generate output with the corpus_formatters.
    # for corpus_formatter in corpus_formatters:
    corpus_results = None
    return corpus, results, corpus_results


@celery.task
def process_text(
    path,
    name=None,
    tokenizer="RegexTokenizer",
    taggers=("DocuscopeTagger",),
    formatters=("StaticHTMLFormatter",),
    corpus_instance=None,
    save=("format_data",),
    save_to_disk=True
):
    """
    Given a path to a text file, process a text using Ity.
    """
    if save is None or (
        "text_str" not in save and
        "tokens" not in save and
        "rules" not in save and
        "tags" not in save and
        "formats" not in save
    ):
        raise ValueError("We're not supposed to save any data? Why are we even generating it, then?")
    # Create a CorpusText instance for this text file.
    text_instance = CorpusText(path, name=name, corpus=corpus_instance)
    # Prep the Ity modules for processing.
    # This is going to look a little weird: "didn't you initialize the modules
    # in process_corpus()?"
    # Yes, we did. the init_tokenizer(), init_tagger(), and init_formatter()
    # functions all check to see if the input is already an instance. If they
    # get a str or a class instead, they'll do the right thing!
    tokenizer = init_tokenizer(tokenizer)
    taggers = [
        init_tagger(tagger)
        for tagger in taggers
    ]
    formatters = [
        init_formatter(formatter)
        for formatter in formatters
    ]
    # Tokenize the text content.
    text_instance.tokens = tokenize_text(text_instance.text_str, tokenizer)
    # Tag this text with the specified Tagger classes.
    for tagger_index, tagger in enumerate(taggers):
        # Raise an exception if we're tagging a second time with [effectively]
        # the exact same tagger---all the same settings that matter and such.
        # (This is why it's important to make sure that Ity modules provide
        # a precise full_label properties.)
        if tagger.full_label in text_instance.tag_data:
            raise ValueError("Needlessly tagging a text with an identically configured tagger for a second time: %s" % tagger.full_label)
        rules, tags = tag_tokens(text_instance.tokens, tagger)
        # Append a dict of information from this tagger.
        text_instance.tag_data[tagger.full_label] = {
            "tags": tags,
            "rules": rules,
            "label": tagger.label,
            "full_label": tagger.full_label
        }
    # Format each tagged output for this text with the specified Formatter classes.
    for formatter_index, formatter in enumerate(formatters):
        # Raise an exception if we're formatting a second time with
        # [effectively] the exact same formatter---all the same settings
        # that matter and such.
        if formatter.full_label in text_instance.format_data:
            raise ValueError("Needlessly formatting a text with an identically configured formatter for a second time: %s" % tagger.full_label)
        # tagger_instance.tag_data may contain the output of multiple taggers.
        # The format_text() function will generate a separate output for each tagger.
        # Also, note that we're not passing the format_text() function the
        # text_str or tokens arguments because we're passing it a CorpusText
        # instance, which has been previously updated above to contain the
        # text's tokens and tag_data. Additionally, the text_str property
        # provides the text file's contents.
        text_instance.format_data = format_text(
            text_instance=text_instance,  # Contains tokens, text_str, and tag_data for one or more taggers
            formatter=formatter,
            save_to_disk=save_to_disk and "formats" in save
        )
    # Return ONLY the processed text results we want by way of the CorpusText instance.
    # This means we're going to clear out the stuff we weren't asked to save.
    # Conditionally add data to the return value.
    # TODO: Add support for writing certain Python data structures to disk (other than Formatters, which will be able to write to disk on their own.)
    if "metadata" not in save:
        text_instance.metadata = None
    if "text_str" not in save:
        text_instance._text_str = None
    if "tokens" not in save:
        text_instance.tokens = []
    if "tag_data" not in save:
        text_instance.tag_data = {}
    if "format_data" not in save:
        text_instance.format_data = {}
    return text_instance

@celery.task
def get_text_str(text_path):
    with codecs.open(text_path, "r", encoding="utf-8") as text_file:
        text = text_file.read()
    return text


@celery.task
def tokenize_text(text, tokenizer="RegexTokenizer"):
    """
    Tokenizes a text string.
    """
    try:
        tokenizer_instance = init_tokenizer(tokenizer)
    except (ValueError, ImportError):
        raise ValueError("Invalid tokenizer module specified.")
    tokens = tokenizer_instance.tokenize(text)
    return tokens


@celery.task
def tag_tokens(tokens, tagger="DocuscopeTagger"):
    """
    Tags a tuple of tokens.
    """
    try:
        tagger_instance = init_tagger(tagger)
    except (ValueError, ImportError):
        raise ValueError("Invalid tagger module specified.")
    tags, tag_maps = tagger_instance.tag(tokens)
    return tags, tag_maps


@celery.task
def format_text(
    tags=None,
    rules=None,
    tokens=None,
    text_str=None,
    text_instance=None,
    formatter="StaticHTMLFormatter",
    save_to_disk=True
):
    # Try to get or otherwise instantiate the formatter module.
    try:
        formatter_instance = initialize_modules([formatter])[0]
    except (ValueError, ImportError):
        raise ValueError("Invalid tagger module specified.")
    # If we're saving the formatted output to disk, figure out where it's going.
    if not save_to_disk:
        output_path = None
        output_name = None
    else:
        if text_instance is not None and hasattr(text_instance, "output_path"):
            # This output path includes the text_instance name in it already.
            output_path = text_instance.output_path
        elif hasattr(text_instance, "corpus") and text_instance.corpus is not None and hasattr(text_instance.corpus, "output_path"):
            output_path = text_instance.corpus.output_path
        else:
            output_path = Ity.corpus_root
        # Okay, we have the output path, but how about the output filename?
        if text_instance is None or not hasattr(text_instance, "name"):
            # Generate a name, I guess.
            output_name = hashlib.sha1()
            output_path = os.path.join(output_path, output_name)
    # Actually call format()!
    format_output = formatter_instance.format(
        output_path=output_path,
        tags=tags,
        rules=rules,
        tokens=tokens,
        text_str=text_str
    )
    return format_output


@celery.task
def get_output_dir(text=None, corpus=None):
    #TODO: Remove this. Blargh.
    output_dir = Ity.output_root
    if corpus is not None and hasattr(corpus, "name"):
        output_dir = os.path.join(output_dir, corpus.name)
    return output_dir


@celery.task
def initialize_modules(modules):
    initialized_modules = {}
    for module_index, module_kwargs in enumerate(modules):
        # Will this module instance be passed a `label` argument?
        if "label" not in module_kwargs:
            module_kwargs["label"] = module_index
        # Anyway, what kind of module is this supposed to be?
        module_instance = None
        if "tokenizer" in module_kwargs:
            module_instance = init_tokenizer(**module_kwargs)
        elif "tagger" in module_kwargs:
            module_instance = init_tagger(**module_kwargs)
        elif "formatter" in module_kwargs:
            module_instance = init_formatter(**module_kwargs)
        # We should definitely have an instantiated module by now.
        if module_instance is None:
            raise ValueError("Invalid Ity module specified: %s" % str(module_kwargs))
        initialized_modules[module_instance.full_label] = module_instance
    return initialized_modules
