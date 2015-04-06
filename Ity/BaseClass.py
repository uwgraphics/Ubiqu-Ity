# coding=utf-8
__author__ = 'kohlmannj'

import abc


class BaseClass(object):
    """
    A very light-weight base class for all Ity classes. Its specific purpose is
    to provide the very simple label and full_label properties, which are
    useful for tracking the provenance of the return values of various Ity
    classes. For example, if two rules returned by two different Taggers' tag()
    methods had the same "name" value, we would be able to determine that they
    do not, in fact, refer to the same rule, because the rules' "full_name"
    values would have swizzled in their Tagger class's full_label properties.

    In general, self._label should be used to set a "human-readable" label for
    the class, while self._full_label should contain additional, non-redundant
    information about the class's return value/s which make it unique. For
    example, we could infer if the output of two classes **should** be
    identical if the class's full_label properties are equal. It's up to those
    classes to swizzle in additional information that will affect its return
    values::

        tokenizer_one = RegexTokenizer(case_sensitive=True)
        tokenizer_two = RegexTokenizer(case_sensitive=False)
        if tokenizer_one.full_label == tokenizer_two.full_label:
            raise StandardError("tokenizer_two's tokenizer() method could\
            produce different output than tokenizer_one.tokenize(), but we\
            can't tell because the implementer didn't update self._full_label.")
        else:
            print "Looks like tokenizer_one and tokenizer_two could have\
            different output, as expected."
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, debug=False, label=None):
        self.debug = debug
        self._label = label
        self._full_label = ""

    @property
    def full_label(self):
        """
        Returns the "full" label for this class instance, based on the class
        name and the value of self._label, if it's something other than None.

        As described in the docstring for BaseClass, this should be a big,
        nasty str which swizzles in all possible settings that might affect the
        output of this class's methods. For example, if an Ity Tokenizer uses
        the value of self.case_sensitive to change what's being returned by
        self.tokenize(), that value (i.e. True or false) should be swizzled in
        to self._full_label.

        :return: The full label for this class instance.
        :rtype: str
        """
        label_parts = [self.__class__.__name__]
        if self._label is not None:
            label_parts.append(
                str(self._label)
            )
        if self._full_label is not None:
            label_parts.append(
                str(self._full_label)
            )
        return ".".join(label_parts)

    @property
    def label(self):
        """
        Returns the "short", or "human-readable" label for this class instance.
        If self._label is None, this property will be set to the class's name.
        :return: The short, "human-readable" label for this class instance.
        :rtype: str
        """
        if self._label is not None:
            return str(self._label)
        else:
            return self.__class__.__name__
