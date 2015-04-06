# coding=utf-8
__author__ = 'kohlmannj'

from Tagger import Tagger
from DocuscopeTagger import DocuscopeTagger
from TopicModelTagger import TopicModelTagger

__all__ = ["Tagger", "DocuscopeTagger", "TopicModelTagger"]

default = DocuscopeTagger
