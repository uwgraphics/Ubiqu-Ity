# coding=utf-8
__author__ = 'ealexand'

import os
import copy
import codecs
from collections import defaultdict
from Ity.Formatters import Formatter
from jinja2 import Environment, FileSystemLoader


class MalletLineGraphFormatter(Formatter):
    """
    An Ity Formatter subclass which outputs SVG-based line graphs for the tags
    returned by a SaliencyTagger's self.tag() method.
    """
    def __init__(
            self,
            debug=None,
            template="standalone.svg",
            partial_template="partial.svg",
            css_file="styles.css",
            js_file=None,
            template_root=None
    ):
        super(MalletLineGraphFormatter, self).__init__(debug)
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
        self.partial_template = self.env.get_template(partial_template)
        self.css_file = css_file
        if self.css_file is not None:
            self.css_path = os.path.join(
                self.template_root,
                self.css_file
            )
        else:
            self.css_path = None
        self.js_file = js_file
        if self.js_file is not None:
            self.js_path = os.path.join(
                self.template_root,
                self.css_file
            )
        else:
            self.js_path = None

    #TODO: change "partial" argument to "options" dict-based argument.
    def format(
        self,
        tags=None,
        tokens=None,
        s=None,
        partial=False,
        pixel_size=50,
        text_name=None,
        summed_area_table=None, # [{topicID: [count, freqRank, salRank, igRank]}, ...]
        rankTypes=None,
        numPages=1,
        included_rules=()
    ):
        # Make sure we have enough data to actually do things.
        if (
            (summed_area_table is None)
        ):
            raise ValueError("Need a summed area table to format the line graph.")
        # Get the window scores.
        window_scores, max_window_scores = self.computeWindowScores(summed_area_table, pixel_size, rankTypes)
        # Figure out if we're using the full or partial template.
        template_to_use = self.template
        if partial:
            template_to_use = self.partial_template

        # Get the contents of the stylesheet.
        css_file = codecs.open(self.css_path, encoding="utf-8")
        css_str = css_file.read()
        css_file.close()

        # Render the template.
        svgs = {}
        for type in rankTypes:
            svgs[type] =  template_to_use.render(
                num_pages=numPages,
                window_scores=window_scores[type],
                pixel_size=pixel_size,
                max_window_score=max_window_scores[type],
                text_name=text_name,
                styles=css_str
            )
        return svgs

    def computeWindowScores(self, sat, pixelSize, rankTypes):
        # I think pixelSize is the number of pixels is the number of steps, basically (assuming 1 step per pixel)
        # Should I include some sort of step size here, too? Or calculate window score at each token?
        numTokens = len(sat)
        stepSize = max(1, numTokens/pixelSize)
        windowSize = 50*stepSize
        topicsToInclude = sat[-1].keys()
        topicIDs = map(lambda x: 'topic_%d' % x, topicsToInclude) # the svg template expects topic IDS
        windowScores = {}
        maxWindowScores = {}
        for type in rankTypes:
            windowScores[type] = {}
            maxWindowScores[type] = 0
            for topicID in topicIDs:
                windowScores[type][topicID] = [0.0 for i in range(numTokens/stepSize + 1)]
        i = 0
        windowCount = 0
        while i < numTokens:
            startIndex = max(0, i - windowSize/2)
            endIndex = min(numTokens - 1, i + windowSize/2)
            indexRange = endIndex - startIndex
            for topic in topicsToInclude:
                for type in rankTypes:
                    typeIndex = rankTypes.index(type) # This is the index within the sat
                    windowScore = (sat[endIndex][topic][typeIndex] \
                                   - sat[startIndex][topic][typeIndex])/float(indexRange)
                    # Update maxWindowScore, maybe.
                    if windowScore > maxWindowScores[type]:
                        maxWindowScores[type] = windowScore
                    windowScores[type]['topic_%d' % topic][windowCount] = windowScore
            i += stepSize
            windowCount += 1
        return windowScores, maxWindowScores
