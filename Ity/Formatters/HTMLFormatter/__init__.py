# coding=utf-8
__author__ = 'kohlmannj'

import os
from Ity.Tokenizers import Tokenizer
from Ity.Formatters import Formatter
from jinja2 import Environment, FileSystemLoader
import logging
import math
import json
from webassets import Environment as WebAssetsEnvironment
from webassets import Bundle
from webassets.ext.jinja2 import AssetsExtension
from webassets.script import CommandLineEnvironment


class HTMLFormatter(Formatter):

    def __init__(
            self,
            debug=None,
            partial_template="partial.html",
            paginated_app_template="paginated.html",
            tags_per_page=750,
            template_root=None
    ):
        super(HTMLFormatter, self).__init__(debug)
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
                'Support.jinja2_htmlcompress.jinja2htmlcompress.HTMLCompress',
                AssetsExtension
            ]
        )
        self.assets_env = WebAssetsEnvironment(
            os.path.join(self.template_root, "standalone"),
            "/standalone"
        )
        self.env.assets_environment = self.assets_env
        # Template Initialization
        self.partial_template = self.env.get_template(partial_template)
        self.paginated_app_template = self.env.get_template(paginated_app_template)
        self.token_strs_index = Tokenizer.INDEXES["STRS"]
        self.webassets_env = WebAssetsEnvironment(
            os.path.join(
                self.template_root,
                "standalone"
            )
        )
        self.standalone_js = Bundle(
            'js/jquery-2.0.2.js',
            'js/app.js',
            filters='rjsmin',
            output='standalone.js'
        )
        self.webassets_env.register('standalone_js', self.standalone_js)
        # Token string index to output
        self.token_str_to_output_index = -1
        self.token_whitespace_newline_str_to_output_index = 0
        # Pagination
        self.tags_per_page = tags_per_page

    def format(self, tokens=None):
        #TODO: Better error condition/s.
        if tokens is None:
            raise ValueError("Not enough valid input data given to format() method.")
        template_to_use = self.partial_template
        return template_to_use.render(
            tokens=tokens
        )

    def format_paginated(self, tags=None, tokens=None, text_name="", text_relative_path="", processing_id=""):
        # First, prepare the tokens
        prepared_tokens = self.prepare_tokens(tokens=tokens, tags=tags)
        # Paginate
        pages_tokens = self.paginate(prepared_tokens, self.tags_per_page)
        pages = map(self.format, pages_tokens)
        # Get the paginated application template. There isn't much template to this.
        args = {
            "title": text_name,
            "text_relative_path": text_relative_path,
            "processing_id": processing_id
        }
        # Prepare tags for javascripting
        prepared_tags = self.prepare_tags(tags[0])
        args["tags"] = json.dumps(prepared_tags)
        args["pages"] = json.dumps(pages)
        paginated_app_output = self.paginated_app_template.render(**args)
        return paginated_app_output

    def _build_webassets(self):
        # Set up a logger
        log = logging.getLogger('webassets')
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.DEBUG)
        cmdenv = CommandLineEnvironment(self.webassets_env, log)
        cmdenv.build()

    def prepare_tokens(self, tokens=None, tags=None):
        """Combine the tokens and tags data structures to make a new structure, listing tokens and
        the tags to belong to if necessary"""
        results = []
        # First, add all tokens to the list
        for t in tokens:
            results.append({'text': t[0][0], 'tag': None, 'pos_start': t[1]})
        # Then, add tags to the tokens that need them
        for t in tags[1]:
            for i in range(t['index_start'], t['index_end'] + 1):
                # Hacky method of getting trimmed tag names
                results[i]['tag'] = t['rules'][0][0].split('.')[-1]
        # Now combine adjacent results with the same tag
        i = 1
        while i < len(results):
            if results[i-1]['tag'] == results[i]['tag']:
                results[i-1]['text'] += results[i]['text']
                results.pop(i)
            else:
                i += 1
        return results

    def paginate(self, tokens, per_page):
        num_pages = int(math.ceil(len(tokens) / (1.0 * per_page)))
        pages = []
        start_pos = 0
        for i in range(0, num_pages):
            pages.append(tokens[start_pos:start_pos + per_page])
            start_pos += per_page
        return pages

    def prepare_tags(self, tags):
        prepared_tags = {}
        for v in tags.values():
            prepared_tags[v['name']] = v
        return prepared_tags