# coding=utf-8
__author__ = 'kohlmannj'

import os
from Ity.Tokenizers import Tokenizer
from Ity.Formatters import Formatter
from jinja2 import Environment, FileSystemLoader


class StaticHTMLFormatter(Formatter):

    # Class-wide Jinja2 environment and templates.
    template_root = os.path.join(
        os.path.dirname(__file__),
        "templates"
    )
    template_name = "content.html"
    standalone_template_name = "standalone.html"
    # Jinja2 Environment initialization.
    # We use the "do" extension to assign Jinja2 variables to the output of
    # Python functions. We also use a third-party extension, "HTMLCompress",
    # to intelligently eliminate whitespace from the final template output.
    env = Environment(
        loader=FileSystemLoader(searchpath=template_root),
        extensions=[
            'jinja2.ext.do',
            'Support.jinja2_htmlcompress.jinja2htmlcompress.HTMLCompress'
        ]
    )
    template = env.get_template(template_name)
    standalone_template = env.get_template(standalone_template_name)
    output_extension = ".html"

    @classmethod
    def dumpStreamToDisk(cls, template_stream, output_path):
        # Make the path absolute to, among other things, eliminate a
        # trailing slash in the path. Also expand ~ into the path to the
        # user's home directory.
        output_path = os.path.abspath(os.path.expanduser(output_path))
        # Does the containing folder exist? If not, create it.
        output_containing_folder_path = os.path.dirname(output_path)
        if not os.path.exists(output_containing_folder_path):
            os.makedirs(output_containing_folder_path)
        # Dump the TemplateStream to disk.
        template_stream.dump(output_path, encoding="utf-8")
        return output_path

    @classmethod
    def prepFormatPagesOutputPath(cls, output_path):
        # Are we supposed to output to disk?
        if output_path is not None:
            # We'll need to output to a folder if we're paginating.
            # Did we get an output path that is to a directory?
            if not os.path.isdir(output_path):
                # Nope, so let's make it a directory path.
                # The line below reassigns output_ext to the extension of
                # whatever file name was previously indicated in
                # format_options["output_path"].
                output_folder_name, output_ext = os.path.splitext(output_path)
                # The new directory path uses the filename, minus extension,
                # of the previously suggested output path.
                output_path = os.path.join(
                    os.path.dirname(output_path),
                    output_folder_name
                )
            # Create the output path folder if it doesn't exist.
            if not os.path.exists(output_path):
                os.makedirs(output_path)
        return output_path, StaticHTMLFormatter.output_extension

    def __init__(
        self,
        debug=False,
        label=None,
        token_str_index=-1,
        token_whitespace_newline_str_index=0,
        standalone=True,
        paginated=False,
        tags_per_page=2000
    ):
        super(StaticHTMLFormatter, self).__init__(debug, label)
        # The index of a token's list of strings to output in the template.
        self.token_str_index = token_str_index
        # The index to use for whitespace and newline tokens. The tokenizer
        # may have condensed tokens containing multiple whitespace / newline
        # characters down to a single string, but it may have also preserved
        # the original strings read from the text (preserve_original_strs = True).
        self.token_whitespace_newline_str_index = token_whitespace_newline_str_index
        self.standalone = standalone
        self.paginated = paginated
        # Note: "paginated" takes precedence over "standalone".
        if self.paginated:
            self.standalone = False
        self.tags_per_page = tags_per_page
        # Determine which template to use.
        if self.standalone:
            self.template = StaticHTMLFormatter.standalone_template
        else:
            self.template = StaticHTMLFormatter.template

    def format(
        self,
        **kwargs
    ):
        if self.paginated:
            return self.formatMultiple(**kwargs)
        else:
            return self.formatSingle(**kwargs)

    def formatSingle(
        self,
        output_path=None,
        rules=None,
        tags=None,
        tokens=None,
        text_str=None
    ):
        # Render the template as a TemplateStream.
        template_stream = self.template.stream(
            paginated=False,
            standalone=self.standalone,
            rules=rules,
            tags=tags,
            tokens=tokens,
            text_str=text_str,
            token_strs_list_index=Tokenizer.INDEXES["STRS"],
            token_type_index=Tokenizer.INDEXES["TYPE"],
            token_types=Tokenizer.TYPES,
            token_str_index=self.token_str_index,
            token_whitespace_newline_str_index=self.token_whitespace_newline_str_index
        )
        # Are we writing to disk?
        if output_path is not None:
            if os.path.isdir(output_path):
                raise ValueError("Output path is to a directory.")
            # See if the output path has an extension. If not, slap the default extension on the end.
            output_name, output_extension = os.path.splitext(output_path)
            if output_extension == "":
                output_path = os.path.join(
                    os.path.dirname(output_path),
                    output_name + StaticHTMLFormatter.output_extension
                )
            # Dump the TemplateStream to disk and return the file path to it.
            return StaticHTMLFormatter.dumpStreamToDisk(template_stream, output_path)
        else:
            # Return the TemplateStream itself.
            return template_stream

    def formatMultiple(
        self,
        output_path=None,
        rules=None,
        tags=None,
        tokens=None,
        text_str=None
    ):
        if tags is None:
            raise ValueError("The tags input argument is required for pagination.")
        # The default output extension, which can be overridden if the
        # output_path is a file path rather than a folder path.
        output_path, output_ext = StaticHTMLFormatter.prepFormatPagesOutputPath(output_path)
        # Render a template for each page of tags.
        page_template = StaticHTMLFormatter.template
        pages = []
        tags_len = len(tags)
        tags_start_index = 0
        page_index = 0
        while tags_start_index < tags_len:
            # Get the end index.
            tags_end_index = tags_start_index + self.tags_per_page
            page_tags = tags[tags_start_index:tags_end_index]
            page_tokens = None
            page_text_str = None
            # Figure out what subset of the tokens we need.
            if tokens is not None:
                tokens_start_index = page_tags[0]["index_start"]
                tokens_end_index = page_tags[-1]["index_end"]
                page_tokens = tokens[tokens_start_index:tokens_end_index]
            # Figure out what subset of the text string we need.
            if text_str is not None:
                text_str_start_index = page_tags[0]["pos_start"]
                text_str_end_index = page_tags[-1]["pos_end"] + page_tags[-1]["token_end_len"]
                page_text_str = text_str[text_str_start_index:text_str_end_index]
            # Render the template for this range of tags.
            page_template_stream = page_template.stream(
                paginated=True,
                standalone=False,
                tags=page_tags,
                rules=rules,
                tokens=page_tokens,
                text_str=page_text_str,
                token_strs_list_index=Tokenizer.INDEXES["STRS"],
                token_type_index=Tokenizer.INDEXES["TYPE"],
                token_types=Tokenizer.TYPES,
                token_str_index=self.token_str_index,
                token_whitespace_newline_str_index=self.token_whitespace_newline_str_index
            )
            # Write to disk if we're indeed outputting to disk.
            if output_path is not None and output_ext is not None:
                page_name = str(page_index) + output_ext
                page_path = os.path.join(output_path, page_name)
                # Append the file path to this page to the pages list.
                pages.append(
                    StaticHTMLFormatter.dumpStreamToDisk(page_template_stream, page_path)
                )
            # Simply append the TemplateStream for this page to the pages list
            # if we're not writing to disk.
            else:
                pages.append(page_template_stream)
            # Increment the page index and the tag index.
            tags_start_index += tags_end_index + 1
            page_index += 1
        # Return the list of file paths (or TemplateStreams) for all the pages.
        return pages
