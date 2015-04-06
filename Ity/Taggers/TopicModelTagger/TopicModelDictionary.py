# coding=utf-8
__author__ = 'kohlmannj'

import os
import csv
from collections import OrderedDict, defaultdict
from Ity import metadata_root, BaseClass
from Ity.Tokenizers import Tokenizer


class TopicModelDictionary(BaseClass):
    """
    Given a path to a folder of topic model data, import said data into Python
    data structures, which are accessible by instance property and through the
    methods self.get_token_props() and self.get_token_props_for_str().

    Note that the metadata, theta, topics, and topic_words are implemented as
    Python properties, meaning that they will be loaded the first time they are
    accessed.
    """
    def __init__(
            self,
            debug=False,
            label=None,
            model_path=None
    ):
        super(TopicModelDictionary, self).__init__(
            debug=debug,
            label=label
        )
        if model_path is None:
            raise ValueError("Attempting to initialize TopicModelDictionary without a model_path value.")
        # Did we get a relative file path?
        if not os.path.isabs(model_path):
            # Try to find this topic model data in Ity.metadata_root.
            model_path = os.path.join(
                metadata_root,
                self.label,
                model_path
            )
        # Does this topic model data exist on-disk, and is it a directory?
        if os.path.exists(model_path) and os.path.isdir(model_path):
            self.model_path = model_path
        else:
            raise ValueError("model_path (%s) either does not exist or is not a directory." % model_path)
        # Pretty snappy to load.
        self._metadata = None
        self._theta = None
        # Slow...we'll do them on first request.
        self._topics = None
        self._topic_words = None

    # Good
    @property
    def metadata(self):
        if self._metadata is None:
            metadata_csv_path = os.path.join(
                self.model_path,
                "metadata.csv"
            )
            metadata_entries = OrderedDict()
            field_names = []
            data_types = []
            # Open the topic model CSV and load it into a Python data structure.
            with open(metadata_csv_path, "rb") as f:
                reader = csv.reader(f)
                for row_index, row in enumerate(reader):
                    if row_index == 0:
                        field_names = row
                    elif row_index == 1:
                        data_types = row
                    else:
                        temp = {}
                        entry_key = None
                        for i in range(len(row)):
                            field_name = field_names[i]
                            field_value = row[i]
                            # Slight transform for text filenames: strip the file path and the
                            # file extension from the value string.
                            if field_name == "filename":
                                field_value = os.path.splitext(
                                    os.path.basename(field_value)
                                )[0]
                                entry_key = field_value
                            temp[field_name] = field_value
                        if entry_key is None:
                            raise StandardError("Attempted to import a metadata entry which has no filename.")
                        metadata_entries[entry_key] = temp
            self._metadata = {
                'metadata': metadata_entries,
                'field_names': field_names,
                'data_types': data_types
            }
        return self._metadata

    # Good
    @property
    def theta(self):
        if self.theta is None:
            theta_csv = os.path.join(
                self.model_path,
                "theta.csv"
            )
            theta_entries = []
            with open(theta_csv, "rb") as f:
                reader = csv.reader(f)
                max_topic = 0
                for text_index, row in enumerate(reader):
                    theta_entries.append({})
                    for i in range(0, len(row), 2):
                        theta_entries[text_index][int(row[i])] = float(row[i+1])
                        max_topic = max(max_topic, int(row[i]))
            self._theta = {
                "theta": theta_entries,
                "num_texts": len(theta_entries),
                "num_topics": max_topic
            }
        return self._theta

    # Okay-ish
    @property
    def topics(self):
        if self.theta is None:
            raise StandardError("Attempting to load individual topic data without any theta data.")
        if self._topics is None:
            self._topics = []
            # Keep track of the total number of words in this topic model.
            total_num_words_in_topic_model = 0
            for topic_num in range(0, self.theta["num_topics"]):
                topic_csv = os.path.join(
                    self.model_path,
                    "topics",
                    'topic_' + str(topic_num) + '.csv'
                )
                with open(topic_csv, 'rb') as f:
                    topic_dict = {
                        "word_list": [],
                        "prop_list": []
                    }
                    reader = csv.reader(f)
                    for row_index, row in enumerate(reader):
                        topic_dict["word_list"].append(row[0])
                        topic_dict["prop_list"].append(float(row[1]))
                    total_num_words_in_topic_model += len(topic_dict["word_list"])
                self._topics.append(topic_dict)
            # Calculate proportions for topic in the topic model.
            for topic_index, topic_dict in enumerate(self._topics):
                topic_dict["topic_model_prop"] = float(len(topic_dict["word_list"])) / total_num_words_in_topic_model
            # Sort topics in descending order according to their .
            self._topics = sorted(
                self._topics,
                key=lambda topic_dict: topic_dict["topic_model_prop"],
                reverse=True
            )
        return self._topics

    # Literally poison (as far as the time it takes)
    @property
    def topic_words(self):
        if self.theta is None:
            raise StandardError("Attempting to load topic data words and props without any theta data.")
        if self.topics is None:
            raise StandardError("Attempting to load topic data words and props without any topic data.")
        if self._topic_words is None:
            # OrderedDicts remember insertion order, which is good.
            self._topic_words = {}
            for topic_num in range(0, len(self.topics)):
                topic_csv = os.path.join(
                    self.model_path,
                    "topics",
                    'topic_' + str(topic_num) + '.csv'
                )
                with open(topic_csv, 'rb') as f:
                    reader = csv.reader(f)
                    for word_index, row in enumerate(reader):
                        word = row[0]
                        prop = float(row[1])
                        # Initialize self._topic_words[word] if we need to.
                        if word not in self._topic_words:
                            # Create the list if we haven't encountered this word before.
                            self._topic_words[word] = []
                            # To Future Joe: It's "proportions", not "probabilities"!
                        topic_prop_tuple = (topic_num, prop)
                        self._topic_words[word].append(topic_prop_tuple)
                # Sort all the lists containing topic_prop_tuples by prop value (index 1), descending.
            for word, word_topic_prop_tuple_list in self._topic_words.items():
                self._topic_words[word] = sorted(
                    word_topic_prop_tuple_list,
                    key=lambda topic_prop_tuple: topic_prop_tuple[1],
                    reverse=True
                )
        return self._topic_words

    # Actually at the core of what I want Couriers to be.
    def get_token_props(self, token, text_name):
        if self.topic_words is None:
            raise StandardError("Attempting to get props for a word before loading topic model words and props.")
        token_props = []
        try:
            text_index = int(self.metadata["metadata"][text_name]["id"])
        except KeyError:
            text_index = -1
        try:
            text_thetas = self.theta["theta"][text_index]
        # If this text isn't in self.theta, just have theta go to zero.
        except IndexError:
            text_thetas = defaultdict(float)
        for token_str in token[Tokenizer.INDEXES["STRS"]][0:1]:
            try:
                token_props = self.topic_words[token_str]
                break
            # Prop values are zero-initialized, so just skip this token_str
            # if it's not in the topic's words list.
            except KeyError:
                continue
        temp_token_props = []
        total_prop_amount = 0.0
        for token_prop_tuple in token_props:
            topic_num = token_prop_tuple[0]
            token_prop = token_prop_tuple[1]
            if topic_num in text_thetas:
                temp_prop = token_prop * text_thetas[topic_num]
                new_token_prop_tuple = (topic_num, temp_prop)
                total_prop_amount += temp_prop
                #new_token_prop_tuple = (topic_num, text_thetas[topic_num])#token_prop * text_thetas[topic_num])
                temp_token_props.append(new_token_prop_tuple)
            # Don't add token_prop_tuples to final_token_props for topics which do not occur in this text.
        # Normalize the token props
        final_token_props = []
        for (topic_num, token_prop) in temp_token_props:
            final_token_props.append((topic_num, token_prop / total_prop_amount))
        # Final pass to sort the final token props
        final_token_props = sorted(final_token_props, key=lambda token_prop_tuple: token_prop_tuple[1], reverse=True)
        return final_token_props

    def get_token_props_for_str(self, token_str, text_name):
        return self.get_token_props([[token_str]], text_name)
