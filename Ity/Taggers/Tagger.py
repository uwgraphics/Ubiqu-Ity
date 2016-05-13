# coding=utf-8
__author__ = 'kohlmannj'

import abc
from Ity.BaseClass import BaseClass
from Ity.Tokenizers import Tokenizer


class Tagger(BaseClass):


    # TODO: Edit this giant comment to reflect new !UNRECOGNIZED and !UNTAGGED scheme
    """
    This is the Ity Tagger base class. It contains an abstract method, tag(),
    which accepts a list of tokens as input (as returned by an Ity
    Tokenizer's tokenize() method) and returns:

    * rules: A dict of dicts representing the semantic rules applied to
             the tags, along with some aggregate information, such as the
             number of tags and tokens with said rule. The top-level dict
             is keyed by the rule's "full name", which is a concatenation
             of the Tagger's full_label property and the rule name itself.
    * tags:  A list of dicts which link one or more rules to the tokens and
             byte positions of text from the original document. Tags may
             also contain some rule-specific metadata.

    Beyond that, Taggers are quite freeform. It's up to the implementer to
    decide how he or she would like to approach pretty much everything,
    especially the nature of the mapping between rules and tags. The Tagger
    data structures support the creation of one-to-many, one-to-one,
    many-to-one, and many-to-many relationships between rules and tokens by
    way of the tags produced.

    There *are* a set of conventions one should use to help standardize the
    return values of self.tag() across different Tagger subclasses, though.
    See "Conventions for Implementing Tagger Subclasses" below for more info.

    "Meta" Rules: "Untagged", "No Rules", and "Excluded"
    ----------------------------------------------------

    The above three "meta" rules are conventions by which Taggers can add
    some semantics to tokens which they don't "understand" or "know about",
    i.e. are incapable of tagging with a valid rule. Returning such tags
    can be omitted if necessary, but sometimes one may be interested in a
    Tagger's "blind spots".

    The following descriptions explain the use case for each of the Ity
    Tagger class's three standard "meta" rules.

    **"Untagged" tags contain tokens for which the Tagger knows nothing.**
    For example, consider a Tagger subclass that uses a dictionary of words
    to determine if a particular rule applies while iterating through the
    list of tokens. In this case, an "untagged" tag would be one which
    contains tokens that do no appear in the Tagger's dictionary.

    **"No Rules" tags contain tokens which the Tagger may "know" about, but
    for which it cannot apply any rules.** Continuing the example presented
    above, a "no rules" tag could occur if a token appears in a Tagger's
    dictionary, but a potential rule cannot be applied because its
    criterion is not satisfied. This could be the case if such a rule could
    only applied to a contiguous sequence of word or punctuation tokens.

    **"Excluded" tags contain tokens which are excluded from tagging, based
    on the Tagger instance's self.excluded_token_types value.**

    Again, the Tagger can omit the tags which only have these "meta" rules
    applied to them, so the "meta" rules are here for diagnostic purposes,
    whether that's for debugging or discovering omissions or logical errors
    in the Tagger's algorithms or data sources.

    Conventions for Implementing Tagger Subclasses
    ----------------------------------------------

    Here are some of the conventions that help standardize the return values
    of self.tag() across different Tagger subclasses:

    * Tagger subclasses should add to the value of self._label if there
      are specific constructor args that affect the retun values of self.tag().
      For example, a Tagger which can use a custom dictionary might swizzle
      in the dictionary's name, e.g. "CustomTagger.MyCustomDictionary.csv"
    * Rules should look like the dict in Tagger.empty_rule (i.e. use copy).
    * Tags should look like the dict in Tagger.empty_tag (i.e. use
      deepcopy, because empty_tag.rules is a list).
    * Rules should have both a (somewhat human-readable) "name" and a
      "full name", which is a period-delimited concatenation of the
      Tagger's full_label property and the rule's "name". This helps avoid
      name collisions with Tagger rules from different Taggers.
    * Tags may include rule-specific metadata by way of their "rules" list,
      which should be a list of 2-tuples, with the first item equal to the
      rule's "full_name" and the second item set to some extra data, such as
      a str, as in this example::

        rule_name = "Example"
        rule.update(
            name=rule_name,
            full_name=".".join([self.full_label, rule_name])
        )
        tag["rules"].append((
            rule["full_name"],
            "Something about this specific occurrence of the 'Foobar' rule."
        ))

    * If the Tagger does not have any rule-specific metadata to append to
      the tag, it should use None as the second item in the 2-tuple described
      above (i.e. ``(rule["full_name"], None)``).
    * For convenience, import the new Tagger subclass in the file
      Ity/Taggers/__init__.py and append the subclass's name to the __all__
      list. This allows other Ity modules to import the class directly without
      importing the identically-named module containing the class::

        # This is kind of ugly.
        from Ity.Taggers.CustomTagger import CustomTagger  # Lame and redundant
        # Import CustomTagger in Ity/Taggers/__init__.py to do this instead:
        from Ity.Taggers import CustomTagger  # Clean and DRY

    * A tag's "pos_end" value should represent the starting byte position of
      the last token in a tag. This could equal the value of "pos_start" for
      a single-token tag. Meanwhile, the tag's "token_end_len" value contains
      the value of ``last_token_in_tag[Tokenizer.INDEXES["LENGTH"]]`` for
      purposes of correctly capturing the range of chars from the original str
      that the tag encapsulates.

    When implementing a Tagger subclass that supports "meta" rules, ensure
    that, for a particular tag:

    * The tag has only one of the three "meta" rules applied to it.
    * The tag never has applied a valid rule in addition to one of the
      three "meta" rules.
    * The tag is only returned by self.tag() if the appropriate value of
      self.return_[untagged, unrecognized, excluded, included]_tags is True.

    When adding rules to the self.rules dict, check to see if the rule's
    full_name is already in self.rules. If so, update the existing rule dict's
    "num_tags" and "num_included_tokens" values (along with any other custom
    values added by a particular Tagger subclass).

    Also, if self.return_[untagged, unrecognized, excluded, included]_tags is
    False, rules returned by self.tag() should **also* omit rule entries
    for the corresponding "meta" rule.

    Given that certain classes of rules and tags can be omitted from the
    return values of self.tag(), it is therefore possible for self.tag() to
    produce **sparse return values**, i.e. a dict of rules and a list of tags
    that do not encapsulate every token in the token list input.

    Tags are meant to contain enough information for other software, such
    as an Ity Formatter, to reference the correct range of characters from
    the original text file. Thus, while order and contiguity are *helpful*
    when working with a list of tags, it is not strictly necessary for
    purposes of reformatting or referencing the original text.
    """
    untagged_rule_name = "!UNTAGGED"
    unrecognized_rule_name = "!UNRECOGNIZED"
    excluded_rule_name = "!EXCLUDED"

    # Note that the name and full_name values are intentionally invalid
    # according to Tagger._is_valid_rule().
    empty_rule = {
        "name": None,
        "full_name": None,
        "num_tags": 0,
        "num_included_tokens": 0
    }

    # Note that the index and pos values in this empty tag are intentionally
    # invalid according to Tagger._is_valid_tag().
    empty_tag = {
        "rules": [],
        "index_start": -1,
        "index_end": -1,
        "len": 0,
        "pos_start": -1,
        "pos_end": -1,
        "token_end_len": 0,
        "num_included_tokens": 0
    }

    def __init__(
        self,
        debug=False,
        label=None,
        excluded_token_types=(),
        case_sensitive=True,
        untagged_rule_name=None,
        unrecognized_rule_name=None,
        excluded_rule_name=None,
        return_untagged_tags=False,
        return_unrecognized_tags=False,
        return_excluded_tags=False,
        return_included_tags=False,
        blacklist=[],
        return_tag_maps=False,
    ):
        """
        The Tagger constructor. Note the defaults---the Tagger base class is
        designed to return all "meta" rules and associated tags by default.

        Make sure you call this in Tagger subclasses' __init__() methods using
        Python 2.7.x's super() function::

            super(CustomTagger, self).__init__(
                debug=debug,
                label=label,
                excluded_token_types=excluded_token_types,
                case_sensitive=case_sensitive,
                untagged_rule_name=untagged_rule_name,
                unrecognized_rule_name=unrecognized_rule_name,
                excluded_rule_name=excluded_rule_name,
                return_untagged_tags=return_untagged_tags,
                return_unrecognized_tags=return_unrecognized_tags,
                return_excluded_tags=return_excluded_tags,
                return_included_tags=return_included_tags
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
        :param untagged_rule_name: The "meta" rule name to use for "untagged"
                                   tags, if they're being returned.
        :type untagged_rule_name: str
        :param unrecognized_rule_name: The "meta" rule name to use for "no rules"
                                   tags, if they're being returned.
        :type unrecognized_rule_name: str
        :param excluded_rule_name: The "meta" rule name to use for "excluded"
                                   tags, if they're being returned.
        :type excluded_rule_name: str
        :param return_untagged_tags: Whether or not to return "untagged" tags
                                     and the "untagged" "meta" rule.
        :type return_untagged_tags: bool
        :param return_unrecognized_tags: Whether or not to return "no rules" tags
                                     and the "no rules" "meta" rule.
        :type return_unrecognized_tags: bool
        :param return_excluded_tags: Whether or not to return "excluded" tags
                                     and the "excluded" "meta" rule.
        :type return_excluded_tags: bool
        :param return_included_tags: Whether or not return "included" tags
                                     and their associated rules.
        :type return_included_tags: bool
        :return: A Tagger instance.
        :rtype Ity.Taggers.Tagger
        """
        super(Tagger, self).__init__(debug, label)
        # Make sure all the excluded token types are of a type that the Ity
        # Tokenizer base class "knows" about. This method raises ValueErrors
        # if it encounters an invalid token type.
        Tokenizer.validate_excluded_token_types(excluded_token_types)
        self.case_sensitive = case_sensitive
        self.excluded_token_types = excluded_token_types
        # The tokens given to self.tag() should be set to this instance field
        # so that private helper methods may have access to them.
        self.tokens = []
        self.token_index = 0
        self.rules = {}
        self.tags = []
        # Should we return tags for which only a particular "meta" rule applies?
        self.return_untagged_tags = return_untagged_tags
        self.return_unrecognized_tags = return_unrecognized_tags
        self.return_excluded_tags = return_excluded_tags
        self.return_included_tags = return_included_tags
        # Support for giving "meta" rules custom names.
        # Either use the name/s given to the constructor, or use this Tagger
        # class's default names.
        if untagged_rule_name is not None:
            self.untagged_rule_name = untagged_rule_name
        else:
            self.untagged_rule_name = Tagger.untagged_rule_name
        if unrecognized_rule_name is not None:
            self.unrecognized_rule_name = unrecognized_rule_name
        else:
            self.unrecognized_rule_name = Tagger.unrecognized_rule_name
        if excluded_rule_name is not None:
            self.excluded_rule_name = excluded_rule_name
        else:
            self.excluded_rule_name = Tagger.excluded_rule_name
        # Append some information to self._full_label.
        self._full_label += ".".join([
            str(setting)
            for setting in [
                self.excluded_token_types,
                self.case_sensitive
            ]
        ] + [
            "EXCL_" + meta_rule_name
            for meta_rule_name in self.excluded_meta_rule_names
        ])

    @property
    def meta_rule_names(self):
        """
        A property containing the list of all "meta" rules.

        :return: A list of "meta" rule names for this class instance.
        :rtype list of strs
        """
        return [
            self.untagged_rule_name,
            self.unrecognized_rule_name,
            self.excluded_rule_name
        ]

    @property
    def excluded_meta_rule_names(self):
        """
        A property containing the list of "meta" rule names which are to be
        excluded from the output of self.tag().

        :return: A list of "meta" rule names (strs) to exclude for this class
                 instance.
        :rtype list of strs
        """
        excluded_meta_rule_names = []
        if not self.return_untagged_tags:
            excluded_meta_rule_names.append(self.untagged_rule_name)
        if not self.return_unrecognized_tags:
            excluded_meta_rule_names.append(self.unrecognized_rule_name)
        if not self.return_excluded_tags:
            excluded_meta_rule_names.append(self.excluded_rule_name)
        return excluded_meta_rule_names

    def _should_return_rule(self, rule):
        """
        A convenient method to determine if self.tag() should return a
        particular rule (and its corresponding tag). It should return it if:

        * The rule's name is NOT in self.excluded_meta_rule_names AND
        * self.return_included_tags is True OR self.return_included_tags is
          False AND the rule name is not one of the meta rules.

        :param rule: A rule dict (looks like Tagger.empty_rule).
        :return: True if the Tagger should return the rule, False otherwise.
        :rtype: bool
        """
        return rule["name"] not in self.excluded_meta_rule_names and (
            self.return_included_tags or (
                not self.return_included_tags and
                rule["name"] in self.meta_rule_names
            )
        )

    def _is_valid_rule(self, rule):
        """
        A convenient method to validate a rule dict. Rule dicts must contain:

        * A "name" key whose value is a str.
        * A "full_name" key whose value is a str which starts with
          self.full_label.
        * A "num_tags" key whose value is a non-negative int.
        * A "num_included_tokens" key whose value is a non-negative int.

        Tagger subclasses should call this method to validate the rules
        they generate.

        :param rule: A rule dict (looks like Tagger.empty_rule).
        :type rule: dict
        :return: True if the rule is valid, False if not.
        :rtype: bool
        """
        return (
            rule is not None and
            "name" in rule and
            type(rule["name"]) is str and
            "full_name" in rule and
            type(rule["full_name"]) is str and
            "num_tags" in rule and
            type(rule["num_tags"]) is int and
            rule["num_tags"] >= 0 and
            "num_included_tokens" in rule and
            type(rule["num_included_tokens"]) is int and
            rule["num_included_tokens"] >= 0
        )

    def _is_valid_tag(self, tag):
        """
        A convenient method to validate a tag dict. Tag dicts must contain:

        * A "rules" key whose value is a non-empty list of 2-tuples.
        * Keys "index_start" and "index_end", where the value of "index_start"
          is a non-negative int less than or equal to "index_end".
        * Keys "pos_start" and "pos_end", where the value of "pos_start" is a
          non-negative int less than or equal to "pos_end".
        * A key "len" whose value represents the number of tokens in the tag,
          set to an int greater than zero.
        * A key "token_end_len" whose value is an int greater than zero.
        :param tag: A tag dict (looks like Tagger.empty_tag).
        :return: True if the tag dict is valid, False otherwise.
        :rtype: bool
        """
        return (
            tag is not None and
            tag["rules"] is not None and
            len(tag["rules"]) > 0 and
            0 <= tag["index_start"] < len(self.tokens) and
            tag["index_start"] <= tag["index_end"] < len(self.tokens) and
            tag["len"] > 0 and
            tag["pos_start"] >= 0 and
            tag["pos_end"] >= 0 and
            tag["pos_start"] <= tag["pos_end"] and
            tag["token_end_len"] > 0
        )

    def _get_nth_next_included_token_index(self, starting_token_index=None, n=1):
        """
        A helper method to get the index of the next token that is not an
        excluded token type, given a starting token index (or self.token_index).

        :param starting_token_index: The index in self.tokens to start at;
                                     if None, we'll use self.token_index.
        :type starting_token_index: non-negative int that's less than
                                    len(self.tokens) or None
        :param n: The nth token from the starting token index.
        :type n: int > 0
        :return: The index of the nth next included token. None if we can't
                 the appropriate index for whatever reason.
        :rtype: non-negative int that's less than len(self.tokens) or None
        """
        if starting_token_index is None:
            starting_token_index = self.token_index
        next_token_index = starting_token_index
        while n > 0:
            next_token_index += 1
            # Don't go beyond the bounds of the tokens list!
            if next_token_index >= len(self.tokens):
                break
            next_token = self.tokens[next_token_index]
            if next_token[Tokenizer.INDEXES["TYPE"]] not in self.excluded_token_types:
                n -= 1
        # Did we actually get the nth next token index?
        if n > 0:
            return None
        else:
            return next_token_index

    @abc.abstractmethod
    def tag(self, tokens):
        """
        An abstract method where all the tagging of the tokens list happens.
        It's recommended to assign the tokens argument to self.tokens
        and (re)set self.token_index to 0 to allow private helper methods to
        easily access these values (and avoid a huge, gross method body here).

        :param tokens: A list of tokens returned by an Ity Tokenizer's
                       tokenize() method.
        :type tokens: list of lists (that look like Ity Tokenizer token lists)
        :return: In order: rule, a dict of dicts (that look like
                 Tagger.empty_rule), and tags, a list of dicts (that look like
                 Tagger.empty_tag).
        :rtype: dict of dicts and list of dicts
        """
        return {}, []
