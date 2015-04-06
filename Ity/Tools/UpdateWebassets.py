__author__ = 'zthomae'

from Ity.Formatters.HTMLFormatter import HTMLFormatter
from Ity.Taggers import DocuscopeTagger
from Ity.Tokenizers.RegexTokenizer import RegexTokenizer
import os
import sys


def build_webassets(output_dir):
    with open('1_KING_HENRY_IV_rev.txt', 'r') as input_file:
        text_contents = input_file.read()
        tokenizer = RegexTokenizer()
        tokens = tokenizer.tokenize(text_contents)
        tagger = DocuscopeTagger(return_included_tags=True)
        tags = tagger.tag(tokens)
        formatter = HTMLFormatter()
        formatter._build_webassets()
        html = formatter.format_paginated(tags=tags, tokens=tokens, text_name="1_KING_HENRY_IV_rev.txt",
                                               text_relative_path="", processing_id="")

    with open(os.path.join(output_dir, 'Ubiqu+Ity_1_KING_HENRY_IV_Docuscope_Example_Output.html'), 'w') as output_file:
        output_file.write(html)

if __name__ == '__main__':
    build_webassets(sys.argv[1])