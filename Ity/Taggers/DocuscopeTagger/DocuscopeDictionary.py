# coding=utf-8
__author__ = 'kohlmann'

"""
DocuscopeJr - read in the DocuscopeDictionary and store it into a handy
class that keeps it for future use

Because a pretty big data structure gets read, we try to be clever about caching.
This makes it a little hard.

A "docuscope dictionary" is a directory with a bunch of stuff in it
over time, these have had different naming conventions

We also don't have great mechanisms for dealing with the file paths
there are some rudimentary mechanisms for finding a useful dictionary

We need to use the same word breaking conventions on rules as we do with
texts (but it doesn't)
"""

# from time import clock
import re
import string
from collections import OrderedDict
from os.path import isdir
# from Ity.Tokenizers import Tokenizer, RegexTokenizer


def getLatFileList(dictionaryDirectory):
    """
    Read in the Lats - return them as a dictionary so we can look them up
    easily and get their info.
    Because we lose the order, we keep the lat index as part of what
    goes into the dictionary
    the triple is ID,Cluster,Dimension
    """

    lats = OrderedDict()
    clusts = OrderedDict()
    dims = OrderedDict()
    count = 0
    clust = ""
    dim = ""
    with openAny(dictionaryDirectory, ["_tones.txt", "tones.txt"]) as f:
        for r in f:
            l = r.split()
            if len(l) > 1:
                if l[0] == "CLUSTER:":
                    clust = l[1]
                    clusts[l[1]] = []
                elif l[0] == "DIMENSION:":
                    dim = l[1]
                    dims[l[1]] = []
                    if clust != "":
                        clusts[clust].append(dim)
                elif l[0] == "LAT:" or l[0] == "CLASS:":
                    lats[l[1]] = (count, clust, dim, l[1:])
                    if dim != "":
                        dims[dim].append(l[1])
                    count = count+1
    return lats, dims, clusts


class DocuscopeDictionary:
    def __init__(self, dictname="default", debug=False):
        self.directory = findDict(dictname)
        self.debug = debug
        self.ruleCount = 0
        # rules are a dictionary only of first words - and these are rules longer than 1
        self.rules = dict()
        # short rules are rules where the word itself is a rule
        self.shortRules = dict()
        self.words = dict()
        # t1 = clock()
        # self.tokenizer = RegexTokenizer(
        #     case_sensitive=False,
        #     excluded_token_types=[
        #         RegexTokenizer.TYPES["WHITESPACE"],
        #         RegexTokenizer.TYPES["NEWLINE"]
        #     ]
        # )

        self.lats, self.dims, self.clusts = getLatFileList(self.directory)

        with openAny(self.directory, ["_wordclasses.txt", "wordclasses.txt"]) as f:
            curClass = "NONE"
            for r in f:
                l = r.split()
                if len(l) == 1:
                    wl = l[0].lower()
                    if not(wl in self.words):
                        self.words[wl] = [wl]
                    self.words[wl].append(curClass)
                elif len(l) == 2:
                    curClass = "!" + l[1].upper()
        for lat in self.lats:
            for latfs in self.lats[lat][3]:
                for suffix in ["", "_p"]:
                    try:
                        with open(makePath(self.directory, latfs+suffix+".txt")) as f:
                            for r in f:
                                li = re.findall(r"[!?\w'-]+|[" + string.punctuation + "]", r)
                                # li = [i for i in WordBreaker(r)]
                                l = map(lambda x: x.upper() if x[0]=='!' else x.lower(), li)
                                # l = []
                                # for x in li:
                                #     # If this word is a special Docuscope keyword, transform it to all uppercase.
                                #     if x[0] == "!":
                                #         l.append(x.upper())
                                #     else:
                                #         # Tokenize the 'word' using RegexTokenizer, as it may have edge punctuation.
                                #         l.extend(
                                #             [token[Tokenizer.INDEXES["STRS"]][0] for token in self.tokenizer.tokenize(x)]
                                #         )
                                ll = len(l)
                                if (ll > 0):
                                    self.ruleCount += 1
                                    for w in l:
                                        if w not in self.words:
                                            self.words[w] = [w]
                                    if len(l) > 1:
                                        if l[0] not in self.rules:
                                            self.rules[l[0]] = dict()
                                        if l[1] not in self.rules[l[0]]:
                                            self.rules[l[0]][l[1]] = []
                                        self.rules[l[0]][l[1]].append((lat, tuple(l)))
                                    else:
                                        self.shortRules[l[0]] = lat
                    except IOError:
                        pass
        # t2 = clock()
        # if self.debug:
        # print "read dictionary in ",t2-t1

    def getRule(self, word):
        """get the rule associated with a word - returns nothing if there aren't any"""
        try:
            return self.rules[word]
        except KeyError:
            return []

    def getWord(self, word):
        if word in self.words:
            return self.words[word]
        else:
            return None

    def syns(self, word):
        try:
            return self.words[word]
        except KeyError:
            return [word]

########################################################################
# stuff for dealing with finding a dictionary - return a full path to the
# directory
dictionarySearchPath = ["..", "../Docuscope", "."]


def findDict(dictname="default"):
    if isdir(dictname):
        return dictname
    else:
        for d in dictionarySearchPath:
            if isdir(makePath(d, dictname)):
                return makePath(d, dictname)
    raise IOError(999, "Can't find Dictionary "+dictname)

########################################################################
# file name utility - lets us be less brittle about slashes


def makePath(dir, file):
    if dir[-1] == "/" or dir[-1] == "\\":
        return dir+file
    else:
        return dir+"/"+file


def openAny(dir, fnames):
    """try a bunch of file names until you find one that exists"""
    for f in fnames:
        try:
            return open(makePath(dir, f), "r")
        except IOError:
            pass
    raise IOError

########################################################################


def getDict(dictn="default", force=False):
    """get the DocuscopeDictionary - if it hasn't been read, read it in"""
    global theDocuscopeDictionary
    if force or ("theDocuscopeDictionary" not in globals()):
        theDocuscopeDictionary = DocuscopeDictionary(dictn)
    return theDocuscopeDictionary
