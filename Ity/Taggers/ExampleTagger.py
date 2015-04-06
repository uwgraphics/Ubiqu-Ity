# coding=utf-8
__author__ = 'kohlmannj'

from copy import copy, deepcopy
from Ity.Tokenizers import Tokenizer
from Ity.Taggers import Tagger


class ExampleTagger(Tagger):
    """
    This is an example Tagger subclass which simply returns a rule named
    "Example", which is applied to word tokens that equal "example"
    (case-insensitive). Thus, it ignores punctuation, whitespace, and newline
    tokens.
    """

    def __init__(
        self,
        debug=True,
        label=None,
        excluded_token_types=(
            Tokenizer.TYPES["PUNCTUATION"],
            Tokenizer.TYPES["WHITESPACE"],
            Tokenizer.TYPES["NEWLINE"]
        ),
        untagged_rule_name=None,
        no_rules_rule_name=None,
        excluded_rule_name=None,
        return_untagged_tags=False,
        return_no_rules_tags=False,
        return_excluded_tags=False,
        return_included_tags=False
    ):
        super(ExampleTagger, self).__init__(
            debug=debug,
            label=label,
            excluded_token_types=excluded_token_types,
            untagged_rule_name=untagged_rule_name,
            no_rules_rule_name=no_rules_rule_name,
            excluded_rule_name=excluded_rule_name,
            return_untagged_tags=return_untagged_tags,
            return_no_rules_tags=return_no_rules_tags,
            return_excluded_tags=return_excluded_tags,
            return_included_tags=return_included_tags
        )
        # This Tagger is always case insensitive.
        self.case_sensitive = False

    def tag(self, tokens):
        for token_index, token in enumerate(tokens):
            # Initialize some data structures.
            rule = copy(self.empty_rule)
            tag = deepcopy(self.empty_tag)
            # Are we excluding this token? Tag it as "excluded" if so.
            if token[Tokenizer.INDEXES["TYPE"]] in self.excluded_token_types:
                rule.update(
                    name=self.excluded_rule_name,
                    full_name=".".join([self.label, self.excluded_rule_name])
                )
            # Is this token's str (in lowercase) equal to "example"?
            elif token[Tokenizer.INDEXES["STRS"]][0].lower() == "example":
                # Cool, it's foobar. Update the rule dict.
                rule_name = "Example"
                rule.update(
                    name=rule_name,
                    full_name=".".join([self.full_label, rule_name])
                )
            # Otherwise, this is an "untagged" tag.
            else:
                rule.update(
                    name=self.untagged_rule_name,
                    full_name=".".join([self.full_label, self.untagged_rule_name])
                )
            # Do we have a valid rule?
            if not self._is_valid_rule(rule):
                raise StandardError("Couldn't generate a valid rule for a tag.")
            # Update the tag by appending a "tag rule tuple", for which the
            # tuple's second value is None (since there's no rule-specific
            # metadata to include).
            tag["rules"].append(
                (rule["full_name"], None)
            )
            # Update other keys in the tag.
            tag.update(
                index_start=token_index,
                index_end=token_index,
                pos_start=token[Tokenizer.INDEXES["POS"]],
                pos_end=token[Tokenizer.INDEXES["POS"]],
                token_end_len=token[Tokenizer.INDEXES["LENGTH"]],
                num_included_tokens=1
            )
            # Validate the tag we just finished making.
            if not self._is_valid_tag(tag):
                raise StandardError("Couldn't generate a valid tag.")
            # Should we return this rule (and its corresponding tag)?
            if self._should_return_rule(rule):
                # Don't replace rules we've already seen; update them instead.
                if rule["full_name"] in self.rules:
                    # Update the existing rule in self.rules.
                    self.rules[rule["full_name"]]["num_tags"] += 1
                    self.rules[rule["full_name"]]["num_included_tokens"] += rule["num_included_tokens"]
                else:
                    # Stick this rule into self.rules if we're supposed to.
                    self.rules[rule["full_name"]] = rule
                # Append the tag to self.tags if we're supposed to (we know
                # we're supposed to if we made it into this block).
                self.tags.append(tag)
