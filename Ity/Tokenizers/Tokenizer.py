# coding=utf-8
__author__ = 'kohlmannj'

import abc
from Ity import BaseClass


class Tokenizer(BaseClass):
    """
    This is the Ity Tokenizer base class. It contains an abstract method,
    tokenize(), which accepts a str as input and returns:

    * tokens, a list of "token" lists, which are light-weight data structures
      containing one or more strs captured from the original str (and/or
      transformed by the Tokenizer), the byte position at which the token
      starts in the original str, the length of the original token str capture,
      and the type of token, e.g. "word", "punctuation", "whitespace",
      or "newline", as defined by an int value from the Tokenizer.TYPES dict.

    Token List Indexes
    ------------------

    Use Tokenizer.INDEXES to retrieve the index in a token list for:

    * Tokenizer.INDEXES["STRS"]: The str or strs corresponding to this token.
    * Tokenizer.INDEXES["POS"]: The starting byte position of this token's
                                original str capture in the original str.
    * Tokenizer.INDEXES["LENGTH"]: The byte length of this token's original
                                   str capture.
    * Tokenizer.INDEXES["TYPE"]: The type of this token, from Tokenizer.TYPES.

    Token Types
    -----------

    Use Tokenizer.TYPES to indicate a token's type:

    * Tokenizer.TYPES["WORD"]: A "word" token, like, an actual English word
                               (or number, I guess).
    * Tokenizer.TYPES["PUNCTUATION"]: A punctuation token, such as ";".
    * Tokenizer.TYPES["WHITESPACE"]: A whitespace token, i.e. a tab or space.
    * Tokenizer.TYPES["NEWLINE"]: A newline token, i.e. "\n".

    Note that RegexTokenizer, the "default" Tokenizer implementation, captures
    congiguous repetitions of "punctuation", "whitespace", and "newline" chars
    as single tokens, i.e. "\n\n\n\n" is captured as a single "newline" token.

    Token Str Transformations and Preserving Original Strs
    ------------------------------------------------------

    Tokenizers may modify the tokens captured from the original text str, which
    is why, for a "token" list named ``token``,
    ``token[Tokenizer.INDEXES["STRS"]]`` is a list. A Tokenizer subclass may
    want to "clean up", transform, and/or otherwise "standardize" the input
    text in one or more ways to return a list of tokens that make Taggers' jobs
    easier. An application using an Ity Tokenizer may want to preserve the
    original str capture for many reasons:

    * The app may want to display the original str capture to users rather than
      the most "cleaned up" version of the token, while providing the "cleaned
      up"/"standardized" token str/s to Taggers.
    * A Tagger subclass might try using the token's multiple strs to determine
      the best possible rule to apply to the token; if a more "raw" str for
      a token doesn't have any rules, perhaps one or more of the "cleaned up"
      strs will fare better.

    Conventions for Implementing Tokenizer Subclasses
    -------------------------------------------------

    * In general, try to avoid creating additional token types. If you really
      feel strongly about adding a new type, I'd say to add it here in the
      Tokenizer base class, because the Tokenizer class method
      validate_excluded_token_types() may be called by a Tagger which has no
      idea which Tokenizer class generated the list of tokens it's processing.
    * RegexTokenizer, the included Tagger implementation, is quite robust, so
      you may not even want or need to implement another Tokenizer, like, ever?
    * You might consider **subclassing** RegexTokenizer to add more str
      transformations on top of its captures and transformations, however.
    * "Token lists" should be always be initialized with the same number of
      items, with ``None`` as the default value::

          token_list = [None] * len(self.INDEXES.keys())

    * Preserving a token's original str capture **and** its entire history of
      str transformations should be an **opt-in** option when implementing
      Tokenizer subclasses, as preserving multiple strs can take up
      significantly more memory.
    * For convenience, import the new Tokenizer subclass in the file
      Ity/Tokenizers/__init__.py and append the subclass's name to the __all__
      list. This allows other Ity modules to import the class directly without
      importing the identically-named module containing the class::

        # This is kind of ugly.
        from Ity.Tokenizers.CustomTokenizer import CustomTokenizer  # Lame and redundant
        # Import CustomTokenizer in Ity/Tokenizers/__init__.py to do this instead:
        from Ity.Tokenizers import CustomTokenizer  # Clean and DRY

    For a Tokenizer subclass, if self.preserve_original_strs is True:

    * The **first** str in ``token[Tokenizer.INDEXES["STRS"]]`` should always
      be the **last transformation** (i.e. the most "standardized" str).
    * The **last** str should be the original str capture (i.e. the most
      "raw" str).

    Additional Comments
    -------------------

    Should "token lists" have been dicts instead? Probably? That might be
    something to refactor in the near future, thus using an "empty_token" dict
    in the same way that Ity Tokenizers have an "empty_tag" dict.
    """
    __metaclass__ = abc.ABCMeta

    # The possible token types.
    TYPES = dict(WORD=0, PUNCTUATION=1, WHITESPACE=2, NEWLINE=3)

    # The indexes of data in a "token list".
    INDEXES = dict(STRS=0, POS=1, LENGTH=2, TYPE=3)

    def __init__(
        self,
        debug=False,
        label=None,
        excluded_token_types=(),
        case_sensitive=True,
        preserve_original_strs=False
    ):
        """
        The Tokenizer constructor. Make sure you call this in Tokenizer
        subclasses' __init__() methods using Python 2.7.x's super() function::

            super(CustomTokenizer, self).__init__(
                debug=debug,
                label=label,
                excluded_token_types=excluded_token_types,
                case_sensitive=case_sensitive,
                preserve_original_strs=preserve_original_strs
            )

        :param debug: Whether or not to print debugging information.
        :type debug: bool
        :param label: The label string identifying this module's return values.
        :type label: str
        :param excluded_token_types: Which token types, from
                                     Ity.Tokenizers.Tokenizer.TYPES, to skip
                                     when tagging.
        :type excluded_token_types: tuple of ints, e.g.
                                    (Tokenizer.TYPES["WHITESPACE"],)
        :param case_sensitive: Whether or not to preserve case when tokenizing.
                               (If self.preserve_original_strs is True, the
                               original case-sensitive capture should also be
                               included.)
        :type case_sensitive: bool
        :param preserve_original_strs: Whether or not to preserve the original
                                       str capture and the transformation
                                       history for each token into
                                       ``token[Tokenizer.INDEXES["STRS"]]``.
        :type preserve_original_strs: bool
        :return: A Tokenizer instance.
        :rtype: Ity.Tokenizers.Tokenizer
        """
        super(Tokenizer, self).__init__(debug, label)
        self.validate_excluded_token_types(excluded_token_types)
        self.excluded_token_types = excluded_token_types
        self.case_sensitive = case_sensitive
        self.preserve_original_strs = preserve_original_strs

    @classmethod
    def validate_excluded_token_types(cls, excluded_token_types):
        """
        A helper method to determine if a tuple or list of excluded token types
        (i.e. ints) is valid. The tuple or list is valid if:

        * All ints in the list are one of the values in the cls.TYPES dict.
        * The number of token types being excluded is less than the number of
          values in the cls.TYPES dict. (It seems pretty useless to have a
          module exclude ALL possible token types, right?)

        :param excluded_token_types: Which token types, from
                                     Ity.Tokenizers.Tokenizer.TYPES, to skip
                                     when tagging.
        :type excluded_token_types: tuple of ints, e.g.
                                    (Tokenizer.TYPES["WHITESPACE"],)
        :return: None
        """
        num_valid_excluded_token_types = 0
        # Make sure the excluded token types are all valid types.
        for token_type in excluded_token_types:
            if token_type not in cls.TYPES.values():
                raise ValueError("Attempting to exclude an invalid token type (%u)." % token_type)
            else:
                num_valid_excluded_token_types += 1
        # Are we going to ignore *every* token type or something?
        # That's, uh, not very useful.
        if num_valid_excluded_token_types >= len(cls.TYPES.keys()):
            raise ValueError("Attempting to exclude all (or more) possible token types.")

    @abc.abstractmethod
    def tokenize(self, s):
        """
        An abstract method where all the tokenizing happens. Returns a list of
        "token lists", which represents all the tokens captured from the input
        str, s.

        The data structure returned looks like this::

           # List of All Tokens
           [
               # Individual Token List
               [
                   # List of token strs, with the "cleaned up" str always at
                   # index 0, and the original str capture always at index -1.
                   [cleaned_up_token_str, [...], original_token_str],
                   original_token_start_position,
                   original_token_str_length
               ]
           ]

        The original token length is included since some tokenize() methods may
        allow the Tokenizer to return a str that isn't the original token str
        from the input str, since the Tokenizer might take steps to correct
        simple formatting artifacts, such as joining two parts of a word split
        across a line break. In this case, other Ity modules, such as a
        Formatter, may use original token length to replace a char range in the
        original str with something new, even if self.preserve_original_strs is
        False.

        Tokenizer subclasses may or may not return whitespace tokens; it's up
        to their defaults and the arguments passed to their constructors, but
        they should set the default of their constructor's excluded_token_types
        argument appropriately.

        :param s: The text to tokenize.
        :type s: str
        :return A list of "token lists".
        :rtype list
        """
        return []
