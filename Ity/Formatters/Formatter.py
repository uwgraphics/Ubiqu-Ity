# coding=utf-8
__author__ = 'kohlmannj'

import abc
from Ity import BaseClass


class Formatter(BaseClass):
    """
    This is the Ity Formatter base class. It contains an abstract method,
    format(), which accepts several input values, including rules, tags,
    tokens, and even the text_str representing the original text, plus an
    optional output_path, and returns:

    * format_output: Either a Formatter-specific data type, or an absolute file
                     path to the file that the Formatter's format() method has
                     written to disk, if the output_path argument is not None.

    Again, different Formatter subclasses will return different values. This is
    potentially poor design, frankly, which is why using the output_path
    argument is strongly recommended---that way, the caller knows it will be
    receiving a file path str.

    Formatters are kind many-headed monsters, as they have free reign over all
    data produced by Ity Tokenizers and Taggers, plus the original text str.
    The tokens and tags lists returned by Ity classes contain enough
    information to reconstruct, for example, an HTML-tagged version of the
    original text using the original token strs (if the tokens were returned by
    a Tokenizer with self.preserve_original_strs = True). The Formatter could
    produce that output using only text_str and a sparse list of tags (meaning
    that there are NOT necessarily tags for every single token or char in the
    text). That said, things can get complicated, so prepare for some confusion
    if you look at, say, StaticHTMLFormatter's Jinja2 templates.

    The Formatters developed for VEP generally required two other fields, which
    are now rolled into this base class: standalone and paginated:

    * **Standalone templates contain all the resources required to display or
      interact with them.**
        * For a Formatter that outputs HTML, for example,
          ``self.standalone = True`` means that the single HTML file returned
          (or written to disk) by self.format() contains all the resources---
          images, data, JavaScript files, etc.---required by the formatted
          output. Essentially, the formatted output is "self-contained".
        * In the same case as above, ``self.standalone = False`` means that the
          HTML output might *not* contain supplementary resources required to
          display or interact with it---instead, a Flask app might be rendering
          the formatted output into a template which *does* load these
          resources.

    * **Paginated** templates output directories.**
    """
    def __init__(
        self,
        debug=False,
        label=None,
        token_str_index=-1,
        token_whitespace_newline_str_index=0,
        standalone=True,
        paginated=False
    ):
        super(Formatter, self).__init__(
            debug=debug,
            label=label
        )
        self.token_str_index = token_str_index
        self.token_whitespace_newline_str_index = token_whitespace_newline_str_index,
        self.standalone = standalone
        self.paginated = paginated

    @abc.abstractmethod
    def format(
        self,
        output_path=None,
        rules=None,
        tags=None,
        tokens=None,
        text_str=None
    ):
        return
