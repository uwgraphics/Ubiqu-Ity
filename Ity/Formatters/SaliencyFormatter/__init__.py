__author__ = 'Eric'

import os
from Ity.Tokenizers import Tokenizer
from Ity.Formatters import Formatter
from jinja2 import Environment, FileSystemLoader


class SaliencyFormatter(Formatter):

    def __init__(self, debug=None, template='standalone.html', template_root=None):
        super(SaliencyFormatter, self).__init__(debug)
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
        if self.debug:
            self.token_str_to_output_index = 0

    def format(self, tags=None, tokens=None, s=None, freqBins=None, igBins=None, salBins=None):
        if (tokens is None):
            pass
        return self.template.render(
            tags=tags,
            tokens=tokens,
            s=s,
            freqBins=freqBins,
            igBins=igBins,
            salBins=salBins,
            token_strs_index=self.token_strs_index,
            token_str_to_output_index=self.token_str_to_output_index
        )