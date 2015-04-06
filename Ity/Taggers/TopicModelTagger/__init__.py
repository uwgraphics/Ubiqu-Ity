# coding=utf-8
__author__ = 'kohlmannj'

import math
from collections import OrderedDict
from copy import deepcopy
from Ity.Tokenizers import Tokenizer
from Ity.Taggers import Tagger
from TopicModelDictionary import TopicModelDictionary
import os


class TopicModelTagger(Tagger):

    def __init__(
        self,
        debug=False,
        label=None,
        excluded_token_types=(
            Tokenizer.TYPES["WHITESPACE"],
            Tokenizer.TYPES["NEWLINE"]
        ),
        case_sensitive=True,
        untagged_rule_name=None,
        no_rules_rule_name=None,
        excluded_rule_name=None,
        return_untagged_tags=False,
        return_no_rules_tags=False,
        return_excluded_tags=False,
        return_included_tags=False,
        text_name=None,
        model_path=None
    ):
        super(TopicModelTagger, self).__init__(
            debug=debug,
            label=label,
            excluded_token_types=excluded_token_types,
            case_sensitive=case_sensitive,
            untagged_rule_name=untagged_rule_name,
            no_rules_rule_name=no_rules_rule_name,
            excluded_rule_name=excluded_rule_name,
            return_untagged_tags=return_untagged_tags,
            return_no_rules_tags=return_no_rules_tags,
            return_excluded_tags=return_excluded_tags,
            return_included_tags=return_included_tags
        )
        if text_name is None:
            raise ValueError("No text_name given.")
        self.text_name = text_name
        if model_path is None:
            raise ValueError("No path to topic model data given.")
        self.model_path = model_path
        # Instantiate a TopicModelDictionary to retrieve information about the topic model.
        self.model = TopicModelDictionary(
            debug=self.debug,
            model_path=model_path
        )
        self.untagged_rule_name = untagged_rule_name
        self.text_name = None
        # Ramp setup
        self.num_ramp_steps = None
        self.min_ramped_value = -1
        self.max_ramped_value = -1
        # Get topic "rules".
        self._rules = OrderedDict()
        # Append additional info to self._full_label.
        self._full_label += ".".join([
            os.path.basename(self.model_path),
            self.text_name
        ])

    def _get_topic_rule_full_name(self, topic_num):
        """
        A convenience method to generate the full name for a topic's rule.

        :param topic_num: The topic number.
        :return: The full name of the rule for this topic number.
        :rtype: str
        """
        return ".".join([
            self.full_label,
            self._get_topic_rule_name(topic_num)
        ])

    def _get_topic_rule_name(self, topic_num):
        """
        No rocket surgery here; just returns a str to use for a topic by its
        topic number.

        :param topic_num:
        :return: The name of the rule for this topic number.
        :rtype: str
        """
        return "topic_%u" % topic_num

    @property
    def rules(self):
        """
        In TopicModelTagger, we're always going to have however many topics
        as rule entries. That doesn't change across calls to self.tag().
        Therefore, we set self.rules once with the available topics.

        :return: An OrderedDict of topic "rules".
        :rtype: dict of dicts
        """
        if self._rules is None:
            for topic_num, topic_dict in enumerate(self.model.topics):
                rule = deepcopy(self.empty_rule)
                rule["name"] = self._get_topic_rule_name(topic_num)
                rule["full_name"] = self._get_topic_rule_full_name(topic_num)
                # Add additional metadata to the rule.
                rule["topic_model_prop"] = topic_dict["topic_model_prop"]
                # We might want some other data available in here, such as the top
                # n words in the topic. Not sure yet.
                # Anyway, stick this rule into self.rules if we're supposed to.
                if not self._is_valid_rule(rule):
                    raise StandardError("Attempting to add an invalid rule!")
                if self.return_included_tags:
                    # Raise an error if there's, somehow, already a topic rule of
                    # the same name in self._rules.
                    if rule["full_name"] in self._rules:
                        raise StandardError("Rule with the full name \"%s\" already in self._rules!" % rule["full_name"])
                    self._rules[rule["full_name"]] = rule
            # Create rules for any "meta" rules we're supposed to include.
            for meta_rule_name in self.meta_rule_names:
                # Skip this "meta" rule if we're supposed to exclude it.
                if meta_rule_name in self.excluded_meta_rule_names:
                    continue
                meta_rule = deepcopy(self.empty_rule)
                meta_rule.update(
                    name=meta_rule_name,
                    full_name=".".join([self.full_label, meta_rule_name]),
                    topic_model_prop=0.0
                )
                if not self._is_valid_rule(meta_rule):
                    raise StandardError("Attempting to add an invalid \"meta\" rule!")
                # Add the "meta" rule.
                self._rules[meta_rule["full_name"]] = meta_rule
        return self._rules

    def _get_tag(self):
        token = self.tokens[self.token_index]
        # Initialize the tag data structure.
        tag = deepcopy(self.empty_tag)
        # Fill it up with some actual data.
        tag["index_start"] = tag["index_end"] = self.token_index
        tag["pos_start"] = tag["pos_end"] = token[Tokenizer.INDEXES["POS"]]
        tag["token_end_len"] = token[Tokenizer.INDEXES["LENGTH"]]
        # All these are single-token tags.
        tag["len"] = 1
        # Get the token str we should look up in the topic model.
        # We'll use the most "cleaned up" token str (index 0) for this.
        token_str = token[Tokenizer.INDEXES["STRS"]][0]
        # Should this be a case-insensitive lookup?
        if not self.case_sensitive:
            token_str = token_str.lower()
        token_props = self.model.get_token_props_for_str(token_str, self.text_name)
        for topic_prop_tuple in token_props:
            topic_num = topic_prop_tuple[0]
            token_topic_prop = topic_prop_tuple[1]
            # Track max and min values.
            if self.min_ramped_value == -1 or self.min_ramped_value > token_topic_prop:
                self.min_ramped_value = token_topic_prop
            if self.max_ramped_value == -1 or self.max_ramped_value < token_topic_prop:
                self.max_ramped_value = token_topic_prop
            # Only add the rule for this topic if the prop value for this
            # token in this topic is greater than zero.
            # The rule tuple contains the topic rule's "full_name" value and
            # the prop value.
            rule_full_name = self._get_topic_rule_full_name(topic_num)
            tag_rule_tuple = (rule_full_name, token_topic_prop)
            if rule_full_name not in self.rules:
                raise StandardError("Attempting to apply a rule that is not in self.rules!")
            else:
                # Increment the count for this rule in self.rules.
                self.rules[rule_full_name]["num_tags"] += 1
                self.rules[rule_full_name]["num_included_tokens"] += 1
            # Append this tag_rule_tuple to the tag's "rules" value.
            tag["rules"].append(tag_rule_tuple)
        # Does this token not appear in any topics?
        if len(tag["rules"]) == 0:
            # Then it gets the "untagged" tag.
            rule_full_name = ".".join([
                self.full_label,
                self.untagged_rule_name
            ])
            tag_rule_tuple = [rule_full_name, 0.0]
            tag["rules"].append(tag_rule_tuple)
        # Is this a valid tag?
        if not self._is_valid_tag(tag):
            raise StandardError("Attempting to append an invalid tag to self.tags!")
        # Append the tag.
        self.tags.append(tag)
        # Update self.token_index.
        self.token_index = self._get_nth_next_included_token_index()

    def tag(self, tokens, text_name=None, num_ramp_steps=3):
        self.text_name = text_name
        self.num_ramp_steps = num_ramp_steps
        # Reset value of num_tags and tags_prop keys in self.rules
        for rule in self.rules.values():
            rule["num_tags"] = 0
            rule["tags_prop"] = 0
        # Reset the value of self.tags.
        self.tags = []
        # Helper methods may need access to the tokens.
        self.tokens = tokens
        # Initialize the token_index value.
        self.token_index = self._get_nth_next_included_token_index(0)
        # Iterate through the tokens and get tags for them.
        while self.token_index < len(self.tokens) and self.token_index is not None:
            self._get_tag()
            if self.debug and self.token_index is not None:
                print "Completed tagging token %u / %u..." % (self.token_index, len(self.tokens))

        # Post-tagging, update "tags_prop" for each tag in self.rules.
        for rule in self.rules.values():
            tags_prop = 0.0
            if len(self.tags) > 0:
                tags_prop = float(rule["num_tag_maps"]) / len(self.tags)
            rule["tags_prop"] = tags_prop
        # Note: the following code is commented out because, well, the caller
        # can handle resorting like a big-boy program, if it wants to.
        # # Resort the rules in descending order according to tags_prop.
        # self._rules = OrderedDict(
        #     sorted(
        #         self._rules.iteritems(),
        #         key=lambda rule: rule["tags_prop"],
        #         reverse=True
        #     )
        # )
        # Post-tagging, set ramp values for all tags' rule-specific metadata,
        # like this:
        # tag["rules"] = [
        #     (rule_full_name, (token_topic_prop, prop_ramp_index))
        # ]
        prop_ramp_step_size = self.max_ramped_value / self.num_ramp_steps
        for tag in self.tags:
            rule_tuples_list = tag["rules"]
            tag["classes"] = []
            if len(rule_tuples_list) > 0 and prop_ramp_step_size > 0:
                for rule_tuple_index, rule_tuple in enumerate(rule_tuples_list):
                    prop_ramp_index = int(math.ceil(rule_tuple[1] / prop_ramp_step_size)) - 1
                    tag["rules"][rule_tuple_index] = (
                        rule_tuple[0],
                        (rule_tuple[1], prop_ramp_index)
                    )
                    rule_tuple.append(prop_ramp_index)
            # Debugging: Add the word's str to the tag.
            if self.debug:
                token_range = self.tokens[tag["index_start"]:(tag["index_end"] + 1)]
                tag["text"] = "".join([token[Tokenizer.INDEXES["STRS"]][0] for token in token_range])
        # Assign self.tags to a local variables so we can clean out self.tags.
        tags = self.tags
        # Clean up some things.
        self.text_name = None
        self.num_ramp_steps = None
        self.min_ramped_value = 0
        self.max_ramped_value = 0
        self.tags = []
        # Return the goods.
        return self.rules, tags
