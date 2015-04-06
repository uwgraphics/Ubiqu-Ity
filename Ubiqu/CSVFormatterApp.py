# coding=utf-8
__author__ = 'kohlmannj'

import os
import codecs
from Ity import corpus_root
from Ity.Utilities import FilePaths
from Ity.Tokenizers import RegexTokenizer
from Ity.Formatters import CSVFormatter
import argparse
from time import time


# From http://stackoverflow.com/a/1305663
class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


# Most of the default arguments for csv_formatter_app(). Callers of csv_formatter_app() should
# copy.deepcopy() this object and fill in the blanks. They should fill in, at minimum:
# * corpus_path
# * output_dir
default_args = dict(
    corpus_path=None,
    filenames=None,
    file_extension="txt",
    tagger_module_name="DocuscopeTagger",
    rules_file=None,
    output_dir=None,
    output_filename=None,
    debug=False,
)
# Convert from a dict to an object.
default_args = Struct(**default_args)


def csv_formatter_app(args):
    # Get the input files with the appropriate file extension.
    patterns = None
    if args.file_extension is not None:
        patterns = ("\." + args.file_extension + "$",)

    # Figure out which tagger we need.
    imported_tagger = getattr(__import__("Ity.Taggers", fromlist=[args.tagger_module_name]), args.tagger_module_name)

    # Make sure the corpus folder at corpus_path exists.
    # If args.corpus_path is an absolute path, os.path.join() will do the right thing.
    corpus_path = os.path.join(
        corpus_root,
        args.corpus_path
    )
    if not os.path.exists(corpus_path):
        raise ValueError("Corpus at path '%s' does not exist.")

    # TopicModelTagger and a few other things may need this.
    corpus_name = os.path.basename(corpus_path)

    # Filter by file names in the corpus.
    if args.filenames is not None and len(args.filenames) > 0:
        for index, filename in enumerate(args.filenames):
            args.filenames[index] = os.path.join(corpus_path, filename)
        input_paths = FilePaths.valid_paths(args.filenames, patterns=patterns, recursion_levels=3, debug=args.debug)
    else:
        input_paths = FilePaths.valid_paths((corpus_path,), patterns=patterns, recursion_levels=3, debug=args.debug)

    ################################
    #### Initialize Ity Modules ####
    ################################

    tokenizer = RegexTokenizer()
    # Instantiate *one* tagger. Note that TopicModelTagger needs a model_path given to it.
    # TODO: Support for multiple taggers.
    # TODO: Run the TopicModel generator for a brand new corpus for which we have no metadata.
    # TODO: It seems like TopicModelTagger implies some kind of CorpusTagger with corpus-specific data. It'd be good to make that a real subclass.
    if args.tagger_module_name == "TopicModelTagger":
        tagger = imported_tagger(corpus_name=corpus_name)
    # Use the rules filename for SimpleRuleTagger if we got one. Otherwise, SimpleRuleTagger will use the rules in "default.csv".
    elif args.tagger_module_name == "SimpleRuleTagger" and args.rules_file is not None:
        tagger = imported_tagger(rules_filename=args.rules_file)
    else:
        tagger = imported_tagger()
    formatter = CSVFormatter()

    # Keep calm and DO THINGS
    tags_list = []
    tokens_list = []
    str_list = []
    text_name_list = []

    # Process each text in the corpus.
    for path_index, path in enumerate(input_paths):
        # Get the name of the text. That appears as output in the CSV.
        text_name = os.path.splitext(os.path.basename(path))[0]
        text_name_list.append(text_name)

        start_time = time()

        # Open the file and get its contents.
        the_file = codecs.open(path, encoding="utf-8")
        the_str = the_file.read()
        the_file.close()
        str_list.append(the_str)

        # Tokenize
        tokens = tokenizer.tokenize(the_str)
        tokens_list.append(tokens)

        # Tag
        tag_data, tag_maps = tagger.tag(tokens)
        tags_list.append([tag_data, tag_maps])

        end_time = time()

        # Debug output
        if args.debug:
            message = "\t** Processed '%s' (%u / %u) in %f seconds. **" % (
                os.path.basename(path),
                path_index + 1,
                len(input_paths),
                end_time - start_time
            )
            print message

    # Output the CSV.
    csv_str = formatter.batch_format(
        tags_list=tags_list,
        tokens_list=tokens_list,
        corpus_name=corpus_name,
        s_list=str_list,
        text_name_list=text_name_list
    )
    # Write the csv_str out to a file.
    if args.output_filename is None:
        csv_filename = corpus_name + "_" + args.tagger_module_name + ".csv"
    else:
        csv_filename = args.output_filename
    # Do we have a specified output directory in the args object?
    if args.output_dir is not None:
        csv_dir = os.path.abspath(
            os.path.expanduser(args.output_dir)
        )
    else:
        # Output the CSV in the current working directory by default.
        csv_dir = os.path.abspath(os.path.dirname(__file__))
    # Create the output directory if it doesn't exist.
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    # Get the full file path to the output CSV.
    csv_path = os.path.join(
        csv_dir,
        csv_filename
    )
    # Write the CSV to disk.
    try:
        csv_file = codecs.open(csv_path, encoding="utf-8", mode="w")
        csv_file.write(csv_str)
        csv_file.close()
        # Debug output
        if args.debug:
            message = "** Wrote CSV containing tagged data for corpus '%s' to '%s'. **" % (corpus_name, csv_path)
            print message
        return csv_path
    except IOError:
        if args.debug:
            message = "**** Error writing out CSV containing tagged data for corpus '%s' to '%s'. ****" % (corpus_name, csv_path)
            print message
        return None


# If this file is directly executed by a Python interpreter, we'll use argparse
# to provide a command line interface to csv_formatter_app().
if __name__ == "__main__":
    #### Parse Input Arguments ####
    parser = argparse.ArgumentParser(description="Output a CSV file containing tag information from a corpus for a specific Ity Tagger module.")
    parser.add_argument('corpus_path', type=str, metavar='PATH',
                        help="The path to a corpus of texts. Either an absolute path, or a path relative to Ity's Data/Corpora folder.")
    parser.add_argument('-f', '--filename', type=str, nargs='+', metavar='FILENAMES', dest='filenames',
                        help="Optionally, one or more text filenames within the specified corpus.")
    parser.add_argument('-e', '--extension', type=str, metavar='EXT', dest='file_extension', default='txt',
                        help="The file extension (*without* leading '.') of the files we want to filter paths by.")
    parser.add_argument('-o', '--output_dir', type=str, metavar='OUTPUT_DIR', dest='output_dir', default='SimpleRuleTagger',
                        help="The output directory for the resulting CSV file.")
    parser.add_argument('-n', '--output_filename', type=str, metavar='OUTPUT_FILENAME', dest='output_filename',
                        help="The output directory for the resulting CSV file.")
    parser.add_argument('-r', '--rules_filename', type=str, metavar='RULES_FILENAME', dest='rules_file',
                        help="The name of rules CSV file to use in Ity/Data/Dictionaries/SimpleRule/, if you're using the SimpleRuleTagger module.")
    parser.add_argument('-t', '--tagger', type=str, metavar='TAGGER_MODULE_NAME', dest='tagger_module_name', default='SimpleRuleTagger',
                        help="The Ity tagger module to use for the CSV output.")
    parser.add_argument('--debug', action='store_true', dest='debug',
                        help="Print debugging output.")
    args = parser.parse_args()

    csv_formatter_app(args)
