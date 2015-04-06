__author__ = 'zthomae'

import os
from Ity.Tokenizers import Tokenizer
from Ity.Formatters import Formatter
from jinja2 import Environment, FileSystemLoader


class LATFormatter(Formatter):

    def __init__(
            self,
            debug=None,
            template="text.html",
            template_root=None
    ):
        super(LATFormatter, self).__init__(debug)
        self.template_root = template_root
        if self.template_root is None:
            self.template_root = os.path.join(
                os.path.dirname(__file__),
                "templates"
            )
        # Jinja2 Environment initialization
        self.env = Environment(
            loader=FileSystemLoader(searchpath=self.template_root),
            extensions=[
                'jinja2.ext.do',
                'Support.jinja2_htmlcompress.jinja2htmlcompress.HTMLCompress'
            ]
        )

        # Template Initialization
        self.template = self.env.get_template(template)
        self.token_strs_index = Tokenizer.INDEXES["STRS"]
        # Token string index to output
        self.token_str_to_output_index = -1
        self.token_whitespace_newline_str_to_output_index = 0

    def format(self, tags=None, tokens=None, input_file=None, s=None):
        #TODO: add arguments for CSS, document title, etc.
        #TODO: Add optional HTML entity encoding.
        #TODO: Do something better about which token string is output.
        # We probably want case-sensitive strings with decoded HTML entities
        # and removed hyphen breaks, but right now there isn't really a good
        # way to specify that. Maybe add an integer indicating the index of
        # the "best" token_str in the token tuple.
        #TODO: Better error condition/s.
        if (
                (tags is None or tokens is None or s is None)
        ):
            raise ValueError("Not enough valid input data given to format() method.")
        template_to_use = self.template
        return template_to_use.render(
            tags=tags,
            tokens=tokens,
            s=s,
            input_file=input_file,
            token_strs_index=self.token_strs_index,
            token_type_index=Tokenizer.INDEXES["TYPE"],
            token_types=Tokenizer.TYPES,
            token_str_to_output_index=self.token_str_to_output_index,
            token_whitespace_newline_str_to_output_index=self.token_whitespace_newline_str_to_output_index,
        )