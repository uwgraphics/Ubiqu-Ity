__author__ = 'zthomae'

import argparse
from BeautifulSoup import BeautifulStoneSoup
import CompareDocuscope
import copy
from Ity.Tokenizers import RegexTokenizer
from Ity.Taggers import DocuscopeTagger
from Ity.Formatters import LATFormatter
import os.path
import pprint
import sys


def make_parser():
    """Constructs and returns the argument parser used in this module"""
    parser = argparse.ArgumentParser(description='<Compare results to known-good ones>')
    parser.add_argument('--type', dest='type', action='store', default=None, help='The type of results to check')
    parser.add_argument('--input', dest='input', action='store', default=(None,), nargs='+', help='The texts to test')
    parser.add_argument('--results', dest='results', action='store', default=(None,), nargs='+',
                        help='The known-good results')
    return parser


def parse_args(parser, args):
    """Wrapper around parse_args for the parser passed in as an argument, for doing input validation"""
    results = parser.parse_args(args)
    if results.type is None:
        raise ValueError('Type not specified')
    if results.input == (None,):
        raise ValueError('Input files not specified')
    if results.results == (None,):
        raise ValueError('Results files not specified')
    return results


def parse_input_files(input_files_list):
    """Constructs a dictionary from a list of files, where the file basenames are the keys and the values
    are dictionaries with information about the input files needed for using them later -- most importantly,
    their full paths"""
    input_files = {}
    for f in input_files_list:
        input_files[os.path.basename(f)] = {
            'fullpath': f
        }
    return input_files


def parse_docuscope_results(results_files_list):
    """Parses a Docuscope output file for the text files it has tags for. A dictionary keyed by file names
    is returned, each associated with a dictionary containing a string representation of the tag tree and
    a value indicating whether the file is present in the input files (initialized to False)"""
    results_files = {}
    for f in results_files_list:
        f_soup = BeautifulStoneSoup(f)
        # Note: everything lowercased after beautifulsoup
        for text in f_soup('annotatedtext'):
            try:
                results_files[text['file']] = {
                    'text': str(text),
                    'present': False
                }
            except KeyError:
                continue
    return results_files


def match_files(input_files, results_files):
    """Takes in results from parse_input_files and parse_docuscope_results and sets the 'present' values
    in the results dictionary to True for all the input files present in it. Does nothing if an input file
    isn't in the docuscope results"""
    job = copy.copy(results_files)
    for f in input_files:
        if f in job:
            job[f]['present'] = True
    return job


def compute_test_pairs(job, input_files, format_function):
    """Takes the outputs of match_files and parse_input_files and constructs a new dictionary with results
    to compare. For all the files in the job that are 'present' and included in input_files, a dictionary entry
    keyed by the file name is created, containing:
    - The 'name' of the file (the key, at the moment),
    - The 'ground_truth' tagging from the results file, and
    - The computed 'test_input' from the supplied format_function, which takes the 'fullpath' of the input file as
      its only argument
    """
    test_pairs = {}
    for f in job:
        if not job[f]['present']:
            continue
        if f not in input_files:
            raise ValueError('Input file %s not found' % f)
        test_pairs[f] = {
            'name': f,
            'ground_truth': job[f]['text'],
            'test_input': format_function(input_files[f]['fullpath'])
        }
    return test_pairs


def compare_test_pairs(test_pairs, compare_function):
    """For each of the entries in test_pairs, the supplied compare_function is run on the 'ground_truth' and
    'test_input' values and added as the 'results' value in a dictionary keyed by the pair 'name'"""
    results = {}
    for pair in test_pairs:
        ground_truth = test_pairs[pair]['ground_truth']
        test_input = test_pairs[pair]['test_input']
        results[test_pairs[pair]['name']] = {'results': compare_function(ground_truth, test_input)}
    return results


def format_ds(input_file):
    """Reads the file at the path pointed at by input_file and returns Docuscope-formatted results from the Ity
    DocuscopeTagger, in string form"""
    with open(input_file, 'r') as f:
        text_contents = f.read()
        tokenizer = RegexTokenizer()
        tokens = tokenizer.tokenize(text_contents)
        tagger = DocuscopeTagger(return_included_tags=True)
        tags = tagger.tag(tokens)
        # do an ugly hack to fix lat names
        for t in tags[1]:
            new_tag = list(t['rules'][0])
            new_tag[0] = new_tag[0].rsplit('.')[-1]
            new_rules = list(t['rules'])
            new_rules.pop(0)
            new_rules.insert(0, new_tag)
            t['rules'] = tuple(new_rules)
        formatter = LATFormatter.LATFormatter()
        return formatter.format(tags=tags, tokens=tokens, s=text_contents, input_file=input_file)


def test_docuscope(args):
    """Runs all the functions necessary after parsing arguments to compare the Docuscope taggings done in the
    Docuscope program and by Ity's DocuscopeTagger"""
    results_list = []
    for results_file in args.results:
        with open(results_file, 'r') as f:
            results_list.append(f.read())
    results_files = parse_docuscope_results(results_list)
    input_files = parse_input_files(args.input)
    job = match_files(input_files, results_files)
    test_pairs = compute_test_pairs(job, input_files, format_ds)
    return compare_test_pairs(test_pairs, CompareDocuscope.compare_results)

if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    if args.type == 'docuscope':
        results = test_docuscope(args)
    else:
        print 'Error: unknown type "%s"' % args.type
        parser.print_usage()
        sys.exit(1)
    pprint.pprint(results)

