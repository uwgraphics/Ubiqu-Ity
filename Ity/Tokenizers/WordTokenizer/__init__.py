# coding=utf-8
from Ity.Tokenizers.WordTokenizer import WordBreaker

__author__ = 'kohlmannj'

from Ity.Tokenizers import Tokenizer
from WordBreaker import WordBreaker


class WordTokenizer(Tokenizer):
    """
    Tokenizes using Mike Gleicher's WordBreaker class. This is strictly a
    wrapper class; you should probably use RegexTokenizer instead.

    :param s: The text to tokenize.
    :type s: str
    :return A list of "token lists".
    :rtype list
    """
    def tokenize(self, s):
        return [tokens for tokens in WordBreaker(s)]
