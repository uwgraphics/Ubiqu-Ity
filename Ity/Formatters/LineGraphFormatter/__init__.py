# coding=utf-8
__author__ = 'kohlmannj'

import os
import copy
import codecs
from collections import defaultdict
from Ity.Formatters import Formatter
from jinja2 import Environment, FileSystemLoader


class LineGraphFormatter(Formatter):
    """
    An Ity Formatter subclass which outputs SVG-based line graphs for the tags
    returned by a TopicModelTagger's self.tag() method. Unfortunately this
    class, as currently written, relies on tag-specific data which only
    TopicModelTagger.tag() returns. That could change, it'd need to be
    refactored to give some kind of weight to individual tags (to make a summed
    area table and thus the actual graph data points).
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
        super(LineGraphFormatter, self).__init__(debug)
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
        pixel_size=None,
        text_name=None,
        included_rules=()
    ):
        if pixel_size is None:
            pixel_size = 50
        # Make sure we have enough data to actually do things.
        if (
            (tags is None or len(tags) != 2)
        ):
            raise ValueError("Not enough valid input data given to format() method.")
        # Do work, son.
        # Get the summed area table.
        #TODO: Add option for winnerTakesAll in format() arguments.
        #summed_area_table = self.getSAT(tags, False, True)
        summed_area_table = self.getSAT(tags, True, False)
        # If included_rules is empty, include all available rules!
        if len(included_rules) == 0:
            included_rules = tags[0].keys()
        # Get the window scores.
        window_scores, max_window_score = self.computeWindowScores(summed_area_table, pixel_size, included_rules)
        # Figure out if we're using the full or partial template.
        template_to_use = self.template
        if partial:
            template_to_use = self.partial_template

        # Get the contents of the stylesheet.
        css_file = codecs.open(self.css_path, encoding="utf-8")
        css_str = css_file.read()
        css_file.close()

        # Render the template.
        return template_to_use.render(
            tag_data=tags[0],
            tag_maps=tags[1],
            window_scores=window_scores,
            pixel_size=pixel_size,
            max_window_score=max_window_score,
            text_name=text_name,
            styles=css_str
        )

    # Returns summed area table over a given tags list.
    # winnerTakesAll: if true, just count top topic
    # props: if true, add up proportions. if false, add up counts.
    def getSAT(self, tags, winnerTakesAll, props):
        numTags = len(tags[0].keys())
        tag_maps = tags[1]
        numTokens = len(tag_maps)
        sat = [0 for i in range(numTokens)]
        currLine = defaultdict(float)
        for i in range(numTokens):
            tagDict = tag_maps[i]
            for (topicID, topicProp, tagRampIndex) in tagDict['rules']:
                # topicNum = int(topicID.split('_')[1])
                currLine[topicID] += topicProp if props else 1
                if winnerTakesAll:
                    break
            sat[i] = copy.deepcopy(currLine)
        return sat

    def computeWindowScores(self, sat, pixelSize, topicsToInclude):
        # Should I include some sort of step size here, too? Or calculate window score at each token?
        # topicsToInclude is a list of topic_keys (i.e. strs)
        windowScores = {}
        numTokens = len(sat)
        stepSize = max(1, numTokens/pixelSize)
        windowSize = 50*stepSize
        maxWindowScore = 0
        for topic in topicsToInclude:
            #windowScores[topic] = [0.0 for i in range(numTokens)]
            windowScores[topic] = [0.0 for i in range(numTokens/stepSize + 1)]
        i = 0
        windowCount = 0
        while i < numTokens:
        #for i in range(numTokens):
            startIndex = max(0, i - windowSize/2)
            endIndex = min(numTokens - 1, i + windowSize/2)
            indexRange = endIndex - startIndex
            for topic in topicsToInclude:
                windowScore = (sat[endIndex][topic] - sat[startIndex][topic])/float(indexRange)
                # Update maxWindowScore, maybe.
                if windowScore > maxWindowScore:
                    maxWindowScore = windowScore
                windowScores[topic][windowCount] = windowScore
            i += stepSize
            windowCount += 1
        return windowScores, maxWindowScore
