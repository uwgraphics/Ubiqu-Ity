# coding=utf-8
__author__ = 'kohlmannj'

import csv
from collections import OrderedDict
from Ity.Tokenizers import Tokenizer
from Ity.Formatters import Formatter
import cStringIO as StringIO


class CSVFormatter(Formatter):

    def __init__(
        self,
        debug=False,
        untagged_rule="!UNTAGGED",
        no_rules_rule="!NORULE",
        excluded_rule="!EXCLUDED"
    ):
        super(CSVFormatter, self).__init__(debug)
        self.output = None
        self.writer = None
        self.untagged_rule = untagged_rule
        self.no_rules_rule = no_rules_rule
        self.excluded_rule = excluded_rule
        self.special_rules = [
            self.untagged_rule,
            self.no_rules_rule,
            self.excluded_rule
        ]

    def format(
        self,
        tags=None,
        tokens=None,
        s=None,
        corpus_name=None,
        text_name=None,
        write_headings=False
    ):
        raise StandardError("format() not implemented, sorry!")

    def batch_format(
        self,
        tags_list=None,
        tokens_list=None,
        s_list=None,
        corpus_name=None,
        corpus_list=None,
        text_name_list=None,
        write_headings=True
    ):
        all_rules = OrderedDict()
        if tags_list is None:
            raise ValueError("No tags_list given to batch_format().")
        # Validate the tags data provided in tags_list.
        for tags in tags_list:
            if (
                tags is None or
                len(tags) != 2 or
                tags[0] is None or
                tags[1] is None
            ):
                raise ValueError("Invalid tagger data in tags_list given to batch_format().")
            # Accumulate a dict of all tags used in the tags_list.
            for rule_full_name, rule in tags[0].items():
                if rule_full_name not in all_rules:
                    all_rules[rule_full_name] = rule
        # We should actually have tags in all_rules now...
        if len(all_rules.keys()) == 0:
            raise StandardError("Accumulated *zero* tags from all the tags in tags_list!")
        # Sort all_rules.
        all_rules = OrderedDict(all_rules.iteritems(), key=lambda rule: rule[""])
        # Check that tags_list, tokens_list, s_list, and text_name_list contain the same number of items.
        # Use tags_list as the canonical count.
        canonical_len = len(tags_list)
        for the_list in [tokens_list, s_list, text_name_list]:
            if the_list is None:
                continue
            if len(the_list) != canonical_len:
                raise ValueError("List of a different length than len(tags_list) given as input to batch_format().")
        # Okay, actually output now.
        self.output = StringIO.StringIO()
        self.writer = csv.writer(self.output)
        # Write the column headings first, if we're supposed to.
        if write_headings:
            row = []
            if text_name_list is not None:
                row.append("Filename")
            if corpus_name is not None or (corpus_list is not None and len(corpus_list) == canonical_len):
                row.append("Corpus")
            # Write out all the tag names except the "untagged" tag.
            for rule_full_name in all_rules.keys():
                if rule_full_name not in self.special_rules:
                    row.append(rule_full_name)
            if tokens_list is not None:
                row.append("<# untagged tokens>")
                row.append("<# no-rules tokens>")
                row.append("<# excluded tokens>")
                row.append("<# word tokens>")
                row.append("<# punctuation tokens>")
                row.append("<# tokens>")
                row.append("<# tag maps>")
            # Write this row.
            self.writer.writerow(row)
        for index, tags in enumerate(tags_list):
            tag_maps = tags[1]
            tag_key_counts = OrderedDict()
            # Find percentages for all tags within this list of tags.
            for rule_full_name in all_rules.keys():
                num_tag_maps_with_tag_key = 0
                for tag_map in tag_maps:
                    tag_key_strs = [tag_key_tuple[0] for tag_key_tuple in tag_map["rules"]]
                    if rule_full_name in tag_key_strs:
                        num_tag_maps_with_tag_key += 1
                if len(tag_maps) > 0:
                    count = num_tag_maps_with_tag_key
                    # percentage = float(num_tag_maps_with_tag_key) / len(tags)
                else:
                    count = 0
                    # percentage = 0.0
                tag_key_counts[rule_full_name] = count
            # Write out a row for the CSV output.
            row = []
            if text_name_list is not None:
                row.append(text_name_list[index])
            if corpus_list is not None and len(corpus_list) == canonical_len:
                row.append(corpus_list[index])
            elif corpus_name is not None:
                row.append(corpus_name)
            # Write out the tag percentages for all tags except the "untagged" and "no rules" tags.
            for rule_full_name, count in tag_key_counts.items():
                if rule_full_name not in self.special_rules:
                    # Multiply the value by 100 for display purposes.
                    if len(tag_maps) > 0:
                        row.append(float(count) / len(tag_maps) * 100)
                    else:
                        row.append(0.0)
            ################
            #### Counts ####
            ################
            # Write out the "untagged", "no rules", and "excluded" token percentages.
            for special_rule in self.special_rules:
                try:
                    # Multiply the value by 100 for display purposes.
                    row.append(tag_key_counts[special_rule])
                except KeyError:
                    row.append("0")
            # Additional counts.
            if tokens_list is not None:
                if tokens_list[index] is not None:
                    # Number of word tokens.
                    row.append(len(
                        [token for token in tokens_list[index] if token[Tokenizer.INDEXES["TYPE"]] == Tokenizer.TYPES["WORD"]]
                    ))
                    # Number of punctuation tokens.
                    row.append(len(
                        [token for token in tokens_list[index] if token[Tokenizer.INDEXES["TYPE"]] == Tokenizer.TYPES["PUNCTUATION"]]
                    ))
                    # Number of tokens.
                    row.append(len(tokens_list[index]))
                # Number of tag maps
                row.append(len(tag_maps))
            # Write this row.
            self.writer.writerow(row)
        # All done, so close the StringIO buffer and return the output as a str.
        output_as_str = self.output.getvalue()
        self.output.close()
        return output_as_str
