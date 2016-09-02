from __future__ import absolute_import
import argparse
import os
import time
from datetime import datetime
from werkzeug.datastructures import ImmutableDict
import ubiq_internal_tasks
from Ity import dictionaries_root



parser = argparse.ArgumentParser(description='Ubiqu+Ity tag_corpus task')
parser.add_argument('corpus_path', help='path to corpus to tag relative to the location of this script')
parser.add_argument('output_path', help='path to output folder relative to the location of this script')
parser.add_argument('--rule_csv', help='flag for corpus rule csv', action='store_true')
parser.add_argument('--rule_per_doc', help='flag for generating a rule csv per document', action='store_true')
parser.add_argument('--ngram_count', help='flag for generating ngram csv, 0 if none, between 1 and 3 for n-grams')
parser.add_argument('--ngram_pun', help='flag for including punctuation characters in ngrams', action='store_true')
parser.add_argument('--ngram_per_doc', help='flag for per-document ngrams', action='store_true')
parser.add_argument('--simple_dictionary_path', help='CSV file containing custom dictionary')
parser.add_argument('--docuscope_version', help='version of DocuScope tagging to use')
parser.add_argument('--chunk', help='divide each text in the corpus into chunks of equal length', action='store_true')
parser.add_argument('--chunk_length', help='the length (in words) of each text chunk')
parser.add_argument('--chunk_offset', help='distance between chunks, must be between 1 and chunk_length')
parser.add_argument('--blacklist_path', help='path to blacklist file relative to the location of this script')
parser.add_argument('--defect_count', help='flag for enabling defect counting for texts from the TCP pipeline', action='store_true')
parser.add_argument('--corpus_name', help='name by which to refer to the corpus')
parser.add_argument('--token_csv', help='flag for an additional csv representation of the tokenized text', action='store_true')



# Ubiquity tag corpus command line tool
# Some of this code is inspired by tasks.get_corpus_info() from revision #62 (deleted by Thomae)

def tagCorpusWithArgs(args):
    # Sanity check dictionaries
    if args.docuscope_version is not None:
        if args.simple_dictionary_path is not None:
            raise ValueError('Cannot specify a Simple Rule dictionary AND a DocuScope version.')
        elif args.docuscope_version not in os.listdir(os.path.join(dictionaries_root,'Docuscope')):
            raise ValueError('Provided docuscope_version %s is not in dictionary directory.' % args.docuscope_version)
    elif args.simple_dictionary_path is not None:
        if os.path.splitext(os.path.basename(args.simple_dictionary_path))[1] != '.csv':
            raise ValueError("Simple Rule dictionary (%s) must be a CSV" % args.simple_dictionary_path)
    else:
        if 'Docuscope' not in os.listdir(dictionaries_root):
            raise ValueError("No Docuscope dictionaries available. Please specify a Simple Rule dictionary for tagging, download a copy of Docusope 3.21 and pass it in as an argument, or use the web client for Docuscope tagging.")

    # Setup corpus_info and corpus_data_files
    timestamp = datetime.now().strftime("%Y-%m-%d-%X").replace(":", "-")
    if args.corpus_name is None:
        if os.path.isdir(args.corpus_path) and (args.corpus_path[-1] == '\\' or args.corpus_path[-1] == '/'):
            args.corpus_name = os.path.basename(args.corpus_path[:-1])
        else:
            args.corpus_name = os.path.basename(args.corpus_path)
    print 'Tagging corpus %s...' % args.corpus_name
    corpus_info = {
        "name": args.corpus_name,
        "job_name":args.corpus_name,
        "provenance": "ubq-%s-%s" % (args.corpus_name, timestamp),
        "path": args.corpus_path,
        "output_path": args.output_path,
        'data': {'Text': {
            'name': 'Text',
            'path': args.corpus_path
        }}
    }
    corpus_data_files = {"Text": {
        'saved': [],
        'skipped': []
    }}
    for root, dirnames, filenames in os.walk(args.corpus_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            file_ext = os.path.splitext(filename)[1]
            if file_ext in ubiq_internal_tasks.DATA_EXTENSIONS['Text']:
                corpus_data_files['Text']['saved'].append(file_path)
            else:
                corpus_data_files['Text']['skipped'].append(file_path)

    # Point to SimpleRule dictionary if supplied
    if args.simple_dictionary_path is not None:
        corpus_info["data"]["SimpleRule"] = {
            "name": "SimpleRule",
            "path": args.simple_dictionary_path
        }
        corpus_data_files["SimpleRule"] = {
            "saved": [args.simple_dictionary_path],
            "skipped": []
        }
    # Run tag_corpus
    # create_zip_archive=True,
    if args.docuscope_version is None:
        ubiq_internal_tasks.tag_corpus(
            corpus_info=corpus_info,
            corpus_data_files=corpus_data_files,
            ngram_count=args.ngram_count,
            ngram_pun=args.ngram_pun,
            chunk_text = args.chunk,
            chunk_length = args.chunk_length,
            chunk_offset = args.chunk_offset,
            blacklist_path = args.blacklist_path,
            rule_csv=args.rule_csv,
            doc_rule=args.rule_per_doc,
            defect_count=args.defect_count,
            ngram_per_doc=args.ngram_per_doc,
            token_csv=args.token_csv
        )
    else:
        ubiq_internal_tasks.tag_corpus(
            corpus_info=corpus_info,
            corpus_data_files=corpus_data_files,
            ngram_count=args.ngram_count,
            ngram_pun=args.ngram_pun,
            tags=ImmutableDict(Docuscope={"dictionary_path": args.docuscope_version}),
            chunk_text = args.chunk,
            chunk_length = args.chunk_length,
            chunk_offset = args.chunk_offset,
            blacklist_path = args.blacklist_path,
            rule_csv=args.rule_csv,
            doc_rule=args.rule_per_doc,
            defect_count=args.defect_count,
            ngram_per_doc=args.ngram_per_doc,
            token_csv=args.token_csv
        )

if __name__ == '__main__':
    args = parser.parse_args()

    tagCorpusWithArgs(args)
