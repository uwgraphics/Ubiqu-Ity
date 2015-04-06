# coding=utf-8
__author__ = 'kohlmannj'

import re
import HTMLParser
from Ity.Tokenizers import Tokenizer


class RegexTokenizer(Tokenizer):
    """
    A Tokenizer subclass that captures several types of tokens using five
    regular expression groups, in the following priority:

    * "Coalesced word fragments", that is, words, and then some. "Words" that
      contain single non-word characters separating other words characters will
      be captured as single tokens. This capture excludes edge punctuation.
      For example: "'tis" is captured as ("'", "tis"), but "north-north-west"
      stays together.
    * "Entities", or strings that each represent a single encoded HTML entity.
      These can sneak into plain text files due to processing errors. There is
      also a flag (convert_entities) that changes them back to the appropriate
      Unicode character/s. Tokenized as type Tokenizer.TYPES["PUNCTUATION"].
    * "Remnants", which captures potentially repeated characters not captured
      by the "coalesced word fragments" regular expression. This means that
      "--" (two consecutive hyphens) is captured as one token, for example.
      Tokenized as type Tokenizer.TYPES["PUNCTUATION"].
    * "Whitespace", which captures non-newline whitespace characters. Again,
      coalescing occurs, so "\t\t\t" or "    " (four spaces) are both captured
      as single tokens (independently of each other, of course).
    * "Newlines", which one or more of "\n", "\r", or "\r\n".

    Output may be customized at instantiation time to disable case-sensitivity
    or have words (yes, words), entities, whitespace, punctuation, or newline
    tokens omitted from the output of self.tokenize() or self.batch_tokenize().
    """

    # The components of the regular expression used to tokenize appear below.
    # They're less scary than they look; I've spread them out for readability
    # and extensively commented each one. These separate pattern strings will
    # be concatenated with "|" between them to form and compile the final
    # regular expression in self.__initialize_tokenize_pattern().

    # "Inner Word Hyphen" Pattern
    # A hyphen placed between two words (unlike a "hyphen break").
    # Used in self._format_token_word() to count the number of "inner word"
    # hyphens; if there are 1 or more, we assume removing the hyphen character
    # in the word's "hyphen breaks" would be a formatting error. This way,
    # "north-\n\tnorth-west" results in "north-north-west" instead of
    # "northnorth-west".
    __pattern_str_inner_word_hyphen = r"\b-\b"

    # "Hyphen Break" Pattern
    # This pattern captures zero or one "hyphen break", i.e., a hyphen and the
    # whitespace between parts of a word split across consecutive lines, e.g.
    # "your-\nself". It's concatenated together with the word fragment pattern
    # in __pattern_str_word_with_hyphen_breaks.
    _pattern_str_hyphen_break = r"""
        (?P<hyphen_break>
            # A hyphen following one or more word characters.
            (?P<hyphen_break_remnant>
                -
            )
            # "Whitespace" between that hyphen and the next word fragment.
            (?P<hyphen_break_whitespace>
                # 0 or more "Not-not-whitespace and not newline" after the hyphen.
                [^\S\n]*
                # 1 or or more newlines.
                \n+
                # 0 or more whitespace characters before the next word fragment.
                \s*
            )
        )
    """

    # "Entity" Pattern
    _pattern_str_entity = r"""
        # "Entity": an HTML entity (i.e. `&amp;` or `&#21512;`) that happens to
        # be hanging out here.
        (?P<entity>
            # An ampersand...
            &
            # Followed by a group that contains either...
            (
                # A pound sign and numbers indicating a hex or decimal unicode
                # entity (i.e. &#x0108; or &#21512;).
                (\#x?\d+)
                # or...
                |
                # Two or more letters, as in an aliased entity (i.e. &amp;).
                # I'm not aware of any name-aliased HTML entities that have
                # single-letter aliases.
                \w\w+
            )
            ;
        )
    """

    # "Word Fragment" Pattern
    # This pattern is used in both the "word with hyphen breaks" and "word"
    # patterns, so it's separated here and concatenated in those patterns to
    # avoid repeating ourselves.
    _pattern_str_word_fragment = r"""
        # A word boundary, which thereby omits edge punctuation.
        \b
        # An ampersand, as might appear in an HTML entity inside a word.
        &?
        # "Interior punctuation": zero or one non-whitespace characters.
        \S?
        # One or more word characters.
        \w+
    """

    # "Word with Hyphen Breaks" Pattern
    # A pattern that captures words, including words with zero or more "hyphen
    # breaks". By default we capture words with hyphen breaks all together as
    # one token, but there will inevitably be cases when we may not want to
    # capture "word, hyphen, whitespace, and another word" as a single token.
    # In those situations, set self.dehyphenate_words to False. Then we'll use
    # __pattern_str_word (below) instead.
    _pattern_str_word_with_hyphen_breaks = r"""
        # One or more "coalesced word fragments".
        # This group captures multiple "fragments" together, so "cap-a-pe", for
        # example, is one capture.
        (?P<word>(
            """ + _pattern_str_word_fragment + """
            # Below we concatenate the hyphen break pattern and add a ? after it.
            # That ? is important---otherwise, we won't correctly match
            # non-hyphen-broken words.
            """ \
                                            + _pattern_str_hyphen_break + """?
        )+)
    """

    # "Word" Pattern
    # The alternate pattern that only captures words without "hyphen breaks".
    # "Interior punctuation" by way of the "\S?" in __pattern_str_word_fragment
    # is still fair game, though.
    _pattern_str_word = r"""
        # One or more "coalesced word fragments".
        # This group captures multiple "fragments" together, so "cap-a-pe", for
        # example, is one capture.
        (?P<word>(
            """ + _pattern_str_word_fragment + """
        )+)
    """

    # "Remnant" Pattern
    _pattern_str_remnant = r"""
        # "Remnants": remaining non-whitespace chars (coalesced if repeated).
        (?P<remnant>
            # This named group captures any non-whitespace character.
            (?P<remnant_char>\S)
            # Captures zero or more of the above "remnant" character.
            (?P=remnant_char)*
        )
    """

    # "Whitespace" Pattern
    _pattern_str_whitespace = r"""
        # "Whitespace": non-newline whitespace.
        (?P<whitespace>
            # This named group captures "not-not-whitespace or not-newline (both kinds)".
            # Hat tip: http://stackoverflow.com/a/3469155/1991086
            (?P<whitespace_char>[^\S\r\n])
            # Captures zero or more of the whitespace character from above.
            (?P=whitespace_char)*
        )
    """

    # "Newline" Pattern
    _pattern_str_single_newline = r"\r\n|(?<!\r)\n|\r(?!\n)"

    _pattern_str_newline = r"""
        # Newlines (coalesced if repeated).
        (?P<newline>
            # (?P<newline_char>\n)
            # Captures zero or more newlines:
            #   * \r\n (CRLF line endings)
            #   * \n without preceding \r
            #   * \r without proceeding \n
            (""" + _pattern_str_single_newline + """)*
        )
    """

    def __init__(self,
         debug=False,
         label=None,
         excluded_token_types=(),
         case_sensitive=True,
         preserve_original_strs=False,
         remove_hyphen_breaks=True,
         convert_entities=True,
         convert_newlines=True,
         condense_whitespace=None,
         condense_newlines=None
    ):
        """
        Instantiates a RegexTokenizer. The initialization options below affect
        the output of the self.tokenize() and self.batch_tokenize() methods.

        self.tokenize() produces a list of lists containing token information.
        Refer to the docstring for self.tokenize() for more details.

        Keyword arguments:
        excluded_token_types-- A tuple of token type integers to exclude from
                               the tokenizer's output. Refer to Tokenizer.TYPES
                               for a dict of valid TYPE integers.
                               (default ())
        case_sensitive      -- Whether or not the tokens from self.tokenize() or
                               self.batch_tokenize() are case-sensitive.
                               (default True)
        preserve_original_strs  -- Whether or not to keep track of a token string's
                               history of transformations, if any. For example,
                               if a token string is dehyphenated, then that
                               token will contain
        remove_hyphen_breaks-- Whether or not to recombine captured words that
                               have been split across consecutive lines.
                               (default True)
        convert_entities    -- Whether or not to convert any captured HTML
                               entities back into Unicode characters. Note that
                               this setting applies to both "word" and "entity"
                               captures, i.e. convert_entities=True and
                               omit_entities=False will still convert any HTML
                               entities found within word captures.
                               (default True)
        omit_words          -- Whether or not to skip "word" tokens. Chances
                               are this won't get used much. (default False)
        omit_entities       -- Whether or not to skip "entity" tokens, which
                               only contain single HTML entities that did not
                               appear "inside" a word capture.
                               (default False)
        omit_whitespace     -- Whether or not to skip tokens entirely
                               consisting of non-newline whitespace characters.
                               (default False)
        omit_remnants       -- Whether or not to skip tokens entirely
                               consisting of non-HTML-entity "remnants" (i.e.
                               punctuation, etc.), so neither words, nor
                               whitespace, nor newline characters.
                               (default False)
        omit_newlines       -- Whether or not to skip tokens entirely
                               consisting of newline characters (i.e. "\n").
                               (default False)
        condense_whitespace -- A string with which to replace the text content
                               of tokens consisting entirely of non-newline
                               whitespace. No condensing occurs if this
                               argument is set to None.
                               (default None)
        condense_newlines   -- A string with which to replace the text content
                               of tokens consisting entirely of newline
                               characters. No condensing occurs if this
                               argument is set to None.
                               (default None)
        """
        super(RegexTokenizer, self).__init__(
            debug=debug,
            label=label,
            excluded_token_types=excluded_token_types,
            case_sensitive=case_sensitive,
            preserve_original_strs=preserve_original_strs
        )
        # Initialize instance fields for later reference.
        self.remove_hyphen_breaks = remove_hyphen_breaks
        self.convert_entities = convert_entities
        self.convert_newlines = convert_newlines
        self.condense_whitespace = condense_whitespace
        self.condense_newlines = condense_newlines
        # Swizzle in the values of several settings for self._full_label.
        self._full_label = ".".join([
            str(setting)
            for setting in [self.excluded_token_types,
                            self.case_sensitive, self.preserve_original_strs,
                            self.remove_hyphen_breaks, self.convert_entities,
                            self.convert_newlines, self.condense_whitespace,
                            self.condense_newlines]
        ])
        # Compile the full tokenization regular expression.
        self.__compile_tokenize_pattern()
        # If we're going to convert entities, we need an HTMLParser instance.
        self.html_parser = None
        if self.convert_entities:
            self.html_parser = HTMLParser.HTMLParser()

    def __compile_tokenize_pattern(self):
        """
        Compiles the regular expression used by self.tokenize() and stores
        a reference to it in self.tokenize_pattern. The full regular expression
        used here is a concatenation of several patterns (as written above
        self.__init__() and conditionally using either the word pattern that
        matches hyphen-broken words, or the pattern that only captures "whole"
        words.

        """
        # Capture hyphen-broken words as single tokens by default.
        word_pattern_str = self._pattern_str_word_with_hyphen_breaks
        # If we're not supposed to remove hyphen breaks, use the alternate word
        # pattern, which doesn't look for "hyphen breaks".
        if not self.remove_hyphen_breaks:
            word_pattern_str = self._pattern_str_word
        # Concatenate the separate pattern strings into the final pattern string.
        # The order here indicates group match priority (i.e. match "words"
        # first, etc.)
        # Join the regex pattern strings with the "or" character ("|").
        final_tokenize_pattern_str = r"|".join([
            word_pattern_str,
            self._pattern_str_entity,
            self._pattern_str_remnant,
            self._pattern_str_whitespace,
            self._pattern_str_newline
        ])
        # Compile the final pattern. Those strings have whitespace, so make
        # sure re.VERBOSE is one of the flags used!
        self.tokenize_pattern = re.compile(final_tokenize_pattern_str, re.I | re.VERBOSE)

    def _format_token_entity(self, m, token_data):
        """
        Modifies the contents of token_data according to how we want to handle
        a token containing an HTML entity. Most of the time we want to convert
        the HTML entity back to unicode characters for both "entity" captures
        and "word" captures.

        Keyword arguments:
        m           -- the regular expression match for the token
        token_data  -- list containing the token data produced from the
                       original regular expression match

        """
        # Convenience variable.
        # ALWAYS use token_strs[0] to modify the current "preferred" token str!
        token_strs = token_data[self.INDEXES["STRS"]]

        # Set the token type in token_data.
        token_data[self.INDEXES["TYPE"]] = self.TYPES["PUNCTUATION"]

        # Make sure we have an HTMLParser instance before continuing.
        if self.html_parser is not None:
            # Find and convert any HTML entities that may be in this token.
            converted_token_str = self.html_parser.unescape(token_strs[0])
            # Should we preserve the original token string (and is the
            # converted token string actually different)?
            if self.preserve_original_strs and converted_token_str != token_strs[0]:
                # Insert rather than replace.
                token_strs.insert(0, converted_token_str)
            else:
                # Replace the token_str instead.
                token_strs[0] = converted_token_str

    def _format_token_word(self, m, token_data):
        """
        Modifies the contents of token_data according to how we want to handle
        a token containing words. We may want to convert HTML entities found in
        the word, make the word case-insensitive (i.e. lowercase), or remove
        "hyphen breaks" from the word as appropriate.

        Keyword arguments:
        m           -- the regular expression match for the token
        token_data  -- list containing the token data produced from the
                       original regular expression match

        """
        # Convert Entities
        # Both word captures may have captured HTML entities "inside" words, so
        # we should be running this on word and entity captures.
        # We have a method for this, so just do that first.
        if self.convert_entities:
            self._format_token_entity(m, token_data)

        # Alright, commence regularly scheduled text processing for words.

        # Convenience variable.
        # ALWAYS use token_strs[0] to modify the current "preferred" token str!
        token_strs = token_data[self.INDEXES["STRS"]]

        # Set the token type in token_data.
        token_data[self.INDEXES["TYPE"]] = self.TYPES["WORD"]

        # Case-Insensitivity
        # Transform the word to lowercase if we're supposed to.
        if not self.case_sensitive:
            token_str_lowercase = token_strs[0].lower()
            # Should we preserve the original string (if it's different)?
            if self.preserve_original_strs and token_str_lowercase != token_strs[0]:
                # Insert rather than replace the lowercase version.
                token_strs.insert(0, token_str_lowercase)
            # Just replace instead.
            else:
                token_strs[0] = token_str_lowercase

        # Remove "Hyphen Breaks"
        # Does this token have a "hyphen break" in it?
        if m.group("hyphen_break") is not None:
            # Should we remove "hyphen breaks"?
            if self.remove_hyphen_breaks:
                # Okay, but only remove the hyphen char if there are zero
                # "inner word hyphens" in the token string.
                # This is a naive test that assumes that if a word contains
                # one or more hyphens that aren't part of a hyphen break
                # group, the hyphen in the hyphen break should be preserved
                # since it's indicative of breaking the word across a
                # newline *and* an actual word with hyphens in it.
                inner_word_hyphens = re.findall(self.__pattern_str_inner_word_hyphen, token_strs[0])
                if len(inner_word_hyphens) == 0:
                    # Remove the text of the hyphen_break groups.
                    token_str = re.sub(self._pattern_str_hyphen_break, "", token_strs[0], flags=re.I | re.VERBOSE)
                else:
                    # Replace the "hyphen breaks" with single hyphens instead.
                    token_str = re.sub(self._pattern_str_hyphen_break, "-", token_strs[0], flags=re.I | re.VERBOSE)
                    # Are we supposed to pass along the original token string?
                if self.preserve_original_strs:
                    token_strs.insert(0, token_str)
                else:
                # Replace the token string instead.
                    token_strs[0] = token_str
            else:
                # How did we match this group? We didn't even look for it.
                raise ValueError("Somehow found a hyphen_break group when we shouldn't have.")

    def _format_token_whitespace(self, m, token_data):
        """
        Modifies the contents of token_data according to how we want to handle
        a token containing whitespace. We may want to "condense" a token
        containing more than one whitespace character down to a single user-
        specified char (i.e. the non-None value of self.condense_newlines).

        Keyword arguments:
        m           -- the regular expression match for the token
        token_data  -- list containing the token data produced from the
                       original regular expression match

        """
        # Convenience variable.
        # ALWAYS use token_strs[0] to modify the current "preferred" token str!
        token_strs = token_data[self.INDEXES["STRS"]]

        # Set the token type in token_data.
        token_data[self.INDEXES["TYPE"]] = self.TYPES["WHITESPACE"]

        # Should we condense this whitespace token (and is this token
        # different than the string we're going to condense it to)?
        if self.condense_whitespace and token_strs[-1] != self.condense_whitespace:
            # Insert the new token string (and keep the original
            # string) if we're supposed to.
            if self.preserve_original_strs:
                token_strs.insert(0, self.condense_whitespace)
            # Replace the token string instead.
            else:
                token_strs[0] = self.condense_whitespace

    def _format_token_newline(self, m, token_data):
        """
        Modifies the contents of token_data according to how we want to handle
        a token containing newlines. We may want to "condense" a token
        containing more than one newline down to a single user-specified char
        (i.e. the non-None value of self.condense_newlines).

        Keyword arguments:
        m           -- the regular expression match for the token
        token_data  -- list containing the token data produced from the
                       original regular expression match

        """
        # for token_list in token_lists:
        # Convenience variable.
        # ALWAYS use token_strs[0] to modify the current "preferred" token str!
        token_strs = token_data[self.INDEXES["STRS"]]

        # Set the token type in token_data.
        token_data[self.INDEXES["TYPE"]] = self.TYPES["NEWLINE"]

        # Should we convert newlines? We'll try to be smart about condensing
        # \r\n into a single newline. Don't do this if the token string is
        # already all \n characters.
        if (
            self.convert_newlines and
            not self.condense_newlines and
            not (reduce(lambda x, y: x & y, [c == "\n" for c in token_strs[-1]]))
        ):
            converted_newlines_string = re.sub(self._pattern_str_single_newline, "\n", token_strs[-1])
            if self.preserve_original_strs:
                token_strs.insert(0, converted_newlines_string)
            # Replace the token string instead.
            else:
                token_strs[0] = converted_newlines_string

        # Should we condense this newline token (and is this token
        # different than the string we're going to condense it to)?
        if self.condense_newlines and token_strs[-1] != self.condense_newlines:
            # Insert and keep the original string if we're supposed to.
            if self.preserve_original_strs:
                token_strs.insert(0, self.condense_newlines)
            # Replace the token string instead.
            else:
                token_strs[0] = self.condense_newlines
                # No other special behavior for newline tokens.

    def tokenize(self, s):
        """
        Returns a list of lists representing all the tokens captured from the
        input string, s.

        The data structure returned looks like this:

        # List of All Tokens
        [
            # List of Data for an Individual Token
            [
                # List of token strings, with the preferred string always at
                # index 0 and the original string always at index -1.
                [preferred_token_str, [...], original_token_str],  # token[0]
                original_token_start_position,                     # token[1]
                original_token_str_length,                         # token[2]
                # An integer from self.TYPES.
                token_type                                         # token[3]
            ]
        ]

        Note that self.batch_tokenize() is not implemented here; the Tokenizer
        superclass will call this subclass's implementation of self.tokenize()
        when invoked.

        Keyword arguments:
        s -- str to tokenize

        """
        tokens = []
        for m in self.tokenize_pattern.finditer(s):
            # The starting byte position of this capture in the original plain
            # text string.
            start = m.start()

            # The text content of the whole capture.
            token_str = m.group()

            # Skip apparently empty captures.
            if token_str == "":
                continue

            # Save the [original] char length of the entire captured string.
            # Don't change this, even if  the token str gets changed, since
            # other tools will use the length value when reformatting a
            # document with the original plain text string and its tokens.
            length = len(m.group())

            # This is the data we'll be outputting for this token.
            # Note that single_token_list[0] is a list of strs, starting with the
            # "preferred" str representation of this token. single_token_list[0][-1]
            # (the last item in the list) always contains the original str
            # capture. Also note that single_token_list[3] (an integer indicating
            # the token type, e.g. self.TYPES.index("WORD") will be added
            # by one of the self._format_token_*() helper methods.
            single_token_list = [None] * len(self.INDEXES.keys())
            single_token_list[self.INDEXES["STRS"]] = [token_str]
            single_token_list[self.INDEXES["POS"]] = start
            single_token_list[self.INDEXES["LENGTH"]] = length

            # Potentially omit certain types of tokens.
            # The technique used to identify token type: if the entire group
            # capture equals the contents of a specific named capture, it's a
            # capture of that type.

            # What kind of token is this, and should we be outputting it?

            # Words
            if (
                m.group("word") is not None and
                Tokenizer.TYPES["WORD"] not in self.excluded_token_types
            ):
                self._format_token_word(m, single_token_list)
            # Entities (Punctuation)
            elif (
                m.group("entity") is not None and
                Tokenizer.TYPES["PUNCTUATION"] not in self.excluded_token_types
            ):
                self._format_token_entity(m, single_token_list)
            # Remnants (Punctuation)
            elif (
                m.group("remnant") is not None and
                Tokenizer.TYPES["PUNCTUATION"] not in self.excluded_token_types
            ):
                # No special behavior for remnant tokens, aside from indicating
                # that they are punctuation tokens.
                single_token_list[self.INDEXES["TYPE"]] = self.TYPES["PUNCTUATION"]
            # Whitespace
            elif (
                m.group("whitespace") is not None and
                Tokenizer.TYPES["WHITESPACE"] not in self.excluded_token_types
            ):
                self._format_token_whitespace(m, single_token_list)
            # Newlines
            elif (
                m.group("newline") is not None and
                Tokenizer.TYPES["NEWLINE"] not in self.excluded_token_types
            ):
                self._format_token_newline(m, single_token_list)
            # We made it to this condition, which means we should NOT add this
            # token to the tokens list. Therefore, `continue`.
            else:
                continue
            # All done, so add the final single_token_list list to the list of tokens.
            tokens.append(single_token_list)
        # Return the goods!
        return tokens
