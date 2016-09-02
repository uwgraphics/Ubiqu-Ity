import argparse
import os
import ubiq_internal_tasks as tasks
from Ity.Tokenizers import RegexTokenizer
from collections import defaultdict
import sys
import csv
import math
from operator import itemgetter


__author__ = 'wintere'

parser = argparse.ArgumentParser(description='Test Ubiqu+Ity tag_corpus task')
parser.add_argument('corpus_path', help='path to corpus to tag relative to the location of this script')
parser.add_argument('output_dir', help='path to output folder relative to the location of this script')
parser.add_argument('ngram_count', help='flag for generating ngram csv, between 1 and 3 for n-grams')
parser.add_argument('--ngram_pun', help='flag for including punctuation characters in ngrams', action='store_true')
parser.add_argument('--per_doc', help='generate per document ngrams', action='store_true')

#companion to tagCorpus.py
#uses Ubiq+Ity standard tokenizer to tokenize and ngrama provided folder of texts
#faster than Ubiq+Ity if only ngrams are desired
def ngramCorpus(args):
    corpus_path = args.corpus_path
    if not os.path.exists(corpus_path):
        raise ValueError("Invalid input corpus input path.", corpus_path, "does not exist on disk.")
    ncount = int(args.ngram_count)
    if ncount > 3 or ncount < 1:
        raise ValueError("Invalid parameter: ngram count must be between 1 and 3.")
    #instantiate tokenizer
    tokenizer = RegexTokenizer()
    tokens = []
    bad_files = []
    #traverse files and tokenize
    documentNgramCounts = defaultdict(int) # to count number of documents ngrams appear in
    corpusNgramCounts = defaultdict(int)
    per_doc_path = None
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    if args.per_doc:
        per_doc_path = os.path.join(args.output_dir, 'perDocNgrams')
        if not os.path.exists(per_doc_path):
            os.mkdir(per_doc_path)
    c = 0
    for dirpath, subdirs, files in os.walk(corpus_path):
        for file in files:
            if '.txt' in file:
                print(c)
                c+=1
                filepath = os.path.join(dirpath, file)
                try:
                    #tokenize
                    tokens = tasks.tokenizeText(filepath, False, None, None, tokenizer)
                    #process out punctuation
                    tokens = tasks.ngramProcess(tokens, args.ngram_pun)
                    # update corpus dictionaries
                    docCounts = tasks.ngramUpdate(tokens, documentNgramCounts, corpusNgramCounts, ncount, args.ngram_pun)
                    if args.per_doc:
                        docName = os.path.splitext(os.path.basename(filepath))[0]
                        ngramCSV(documentNgramCounts=None, corpusNgramCounts=docCounts, maxN=ncount, output_dir=per_doc_path, name=docName, doc=True)
                except NotImplementedError:
                    bad_files.append(filepath)
    ngramCSV(documentNgramCounts=documentNgramCounts, corpusNgramCounts=corpusNgramCounts, maxN=ncount, output_dir=args.output_dir, name=os.path.basename(corpus_path), doc=False)
    print("Completed ngram processing of corpus " + os.path.basename(corpus_path))
    if bad_files != []:
        print("Unable to ngram the following files" + str(bad_files))


#given dictionaries representing corpus and document frequencies, outputs ngram statistics to csv
#one csv for each k-gram
def ngramCSV(corpusNgramCounts, documentNgramCounts, maxN,output_dir,name, doc):
    fds = []
    writers = []
    rank = [0] * maxN
    prevCount = [sys.maxsize] * maxN
    # open and initialize ngram csvs
    for i in range(1, maxN + 1):
        path = os.path.join(output_dir, name + '-' + str(i) + 'grams.csv')
        f = open(path, 'wb')
        w = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        if doc:
            w.writerow(["ngram", "document frequency", "rank in document"])
        else:
            w.writerow(["ngram", "corpus frequency", "document frequency", "rank in corpus"])
        fds.append(f)
        writers.append(w)

    # rank and print ngrams
    cc = lambda (a1, a2), (b1, b2):cmp((b2, a1), (a2, b1))
    for key, value in sorted(corpusNgramCounts.iteritems(), cmp=cc):
        n = len(key) - 1
        if value < prevCount[n]:
            rank[n] += 1
            prevCount[n] = value
        if doc:
            row = [' '.join(key), value, rank[n]]
        else:
            row = [' '.join(key), value, documentNgramCounts[key], rank[n]]
        writers[n].writerow(row)

    for fd in fds:
        fd.close()


if __name__ == '__main__':
    args = parser.parse_args()
    ngramCorpus(args)
