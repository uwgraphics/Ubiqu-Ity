# coding=utf-8
__author__ = 'kohlmannj'

import os
import codecs
import csv
from Ity import dictionaries_root
from Ity import BaseClass


class DocuscopeCSVDictionary(BaseClass):

    def __init__(
        self,
        debug=False,
        label=None,
        rules_filename="default.csv",
        case_sensitive=False
    ):
        super(DocuscopeCSVDictionary, self).__init__(
            debug, label
        )
        self.case_sensitive = case_sensitive
        self.rules_file = rules_filename
        if self.rules_file is None:
            raise ValueError("Attempting to initialize DocuscopeCSVDictionary without a rules_filename.")
        # See if the rule_file_name exists on-disk.
        self.rules_path = os.path.join(
            dictionaries_root,
            self.label,
            self.rules_file
        )
        if not os.path.exists(self.rules_path):
            raise ValueError("Attempting to instantiate a DocuscopeCSVDictionary with a nonexistent rules_filename.")
        self.rules = {}
        self.tokens_in_rules = set()
        self.shortRules = {}
        self.words = dict()

    def _load_rules(self):
        if len(self.rules.keys()) > 0:
            raise StandardError("Needlessly reloading rules file? Huh?")
        # Load the rules CSV file.
        rules_file = codecs.open(self.rules_path, encoding="utf-8")
        reader = csv.reader(rules_file)
        for row_index, row in enumerate(reader):
            # Remove trailing whitespace.
            row = [col.strip() for col in row]
            # Skip the first row if it's the column headings (case-insensitive).
            if row_index == 0 and [str(col).lower() for col in row] == ["words", "rule"]:
                continue
            # Import this row using simple whitespace splitting.
            # The str.split() method without an argument splits on whitespace.
            words = row[0].split()
            # Transform the words column to lowercase if we don't care about case sensitivity.
            if not self.case_sensitive:
                words = tuple(str(word).lower() for word in words)
            rule = row[1]
            rule_tuple = (rule, words)
            # Skip "empty" rules.
            if len(words) == 0:
                continue
            # Put in self.words
            for w in words:
                self.words[w] = [w]
            # Insert this rule into either the rules dict or the shortRules dict.
            rule_root_key = words[0]
            # Should this be a short rule?
            if len(words) == 1:
                # Assume there can only be one short rule per word
                self.shortRules[rule_root_key] = rule
            # Guess not, so it's a long rule.
            else:
                rule_next_key = words[1]
                if rule_root_key not in self.rules:
                    self.rules[rule_root_key] = {}
                if rule_next_key not in self.rules[rule_root_key]:
                    self.rules[rule_root_key][rule_next_key] = []
                self.rules[rule_root_key][rule_next_key].append(rule_tuple)
            # Stick this rule's words into the self.tokens_in_rule set.
            self.tokens_in_rules.update(words)
