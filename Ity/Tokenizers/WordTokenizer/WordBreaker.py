# coding=utf-8
"""
Heads up: this is a refactored version of gleicher's WordBreaker.

Instead of returning strings, it returns dictionaries containing "word" and "startPos" keys.

Docucscope Jr - the Naive Way!

Utilities for breaking texts into words. based on lots of assumptions.

Note: The WordBreaker creates an iterator that lets you loop over the words in
a string. At present, there is no real way to connect it to a file, so you have
to read in the whole text.

This makes a vain attempt to mimic Docuscope's word breaking rules, which 
may be a bit problematic. dashes are always part of words. single quotes are
part of words, except at the beginning and end

TODO:
    - Make WordBreaker work from a file without reading the whole text
    - Be smarter about quotes
    - Be smarter about punctuation
    - Deal with the mysteries of weird characters

Created on Sun Nov 27 11:46:49 2011

@author: gleicher
"""
import string


def myisspace(c):
    if c==' ' or c=='\t':
        return True
    else:
        return False


def validletter(c):
    return c.isalnum() or c == '-' or c=="'"


class WordBreaker():
    """class for breaking a string into a sequence of words"""
    def __init__(self, _str):
        """create a WordBreaker for a given string"""
        self.str = _str
        self.strl = len(_str)
        self.pos = 0
    def __iter__(self):
        """this is required so that python knows that it can be iterated over"""
        return self
    def peek(self):
        """return the current character. if it's something weird, then advance"""
        c = self.str[self.pos]
        if c=='|' or c=='_' or ord(c)>127:
            self.pos = self.pos +1
            return self.peek()
        return c
    def unpeek(self,char):
        """put the character back (or at least try) - no error checking!"""
        if (self.pos > 0):
            self.pos -= 1
    def getchar(self):
        c = self.peek()
        self.pos = self.pos + 1
        return c
    def next(self):
        """This is the main thing that does the iteration"""
        if self.pos >= self.strl:
            raise StopIteration
        strc = []
        # catch IndexError (if we go off the end of the string)
        try:
            # skip any spaces
            while myisspace(self.peek() ):
                self.pos = self.pos+1
            # the first character decides what "class" we are in
            c = self.getchar()
            strc.append(c)
            # a linefeed is something all to itself
            if c=='\n' or c=='\r':
                # note - this turns multiple linefeeds into single linefeeds
                # maybe a bad idea?
                while self.peek() == c:
                    self.pos = self.pos+1
                return [["\n"], self.pos - 1, 1]
            # we need to be a little careful with the ampersand - it might be an
            # HTML code, or it might be an ampersand
            # so look ahead for the semicolon
            if c=='&':
                try:
                    for i in range(8):
                        if self.str[self.pos+i]==';':
                            raise KeyError
                except KeyError:
                    while c!=';':
                        c=self.getchar()
                        strc.append(c)
                    return [["".join(strc)], self.pos - len(strc), len(strc)]
                except IndexError:
                    pass
                return [["&"], self.pos - 1, 1]
            # a piece of punctuation goes by itself - a linebreak is a punctuation
            # note: Docuscope treats dashes as part of a word
            if c in string.punctuation and c!='-':
                # eat up repetition (emdash, ellipsis, ...)
                while self.peek() == c:
                    self.pos = self.pos+1
                    strc.append(c)
                return [["".join(strc)], self.pos - len(strc), len(strc)]
            # stop when you get to something fishy
            c = self.peek()
            while validletter(c):
                strc.append(c)
                self.pos += 1
                c = self.peek()
            # Docuscope says an apostrophe at the end is a separate token
            if strc[-1] == "'":
                strc.pop()
                self.unpeek("'")
            return [["".join(strc).lower()], self.pos - len(strc), len(strc)]
        except IndexError:
            if len(strc) > 0:
                self.pos=self.strl
                return [["".join(strc)], self.pos - len(strc), len(strc)]
            else:
                raise StopIteration
