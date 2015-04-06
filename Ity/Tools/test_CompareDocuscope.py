from unittest import TestCase
from Ity.Tools import CompareDocuscope

__author__ = 'zthomae'


class TestReadText(TestCase):
    def setUp(self):
        self.example_text = """<AnnotatedText File="test.txt">
                <A LAT="LongRule1">two words</A>
                ,
                <A LAT="ShortRule1">two</A>
                <A LAT="ShortRule2">words</A>
        </AnnotatedText>"""
        self.annotated_text = CompareDocuscope.read_text(self.example_text)

    def test_should_read_all_anchor_elements(self):
        if not len(self.annotated_text) == 3:
            self.fail("read_text should return a structure with all the tags in it")

    def test_should_read_all_lats(self):
        if not map(lambda x: x['lat'], self.annotated_text) == ['LongRule1', 'ShortRule1', 'ShortRule2']:
            self.fail("read_text should return a structure with all the LATs in it")

    def test_should_read_all_words(self):
        if not map(lambda x: x['tag'], self.annotated_text) == ['two words', 'two', 'words']:
            self.fail("read_text should return a structure with all the tagged words in it")


class TestCompareResults(TestCase):
    def setUp(self):
        self.first_text = """<AnnotatedText File="test.txt">
                <A LAT="LongRule1">two words</A>
                ,
                <A LAT="ShortRule1">two</A>
                <A LAT="ShortRule2">words</A>
        </AnnotatedText>"""

        self.second_text = """<AnnotatedText File="test.txt">
                <A LAT="LongRule2">two words</A>
                <A LAT="CommaRule">,</A>
                <A LAT="ShortRule1">two</A>
                <A LAT="ShortRule2">words</A>
        </AnnotatedText>"""

        self.results = CompareDocuscope.compare_results(self.first_text, self.second_text)

    def test_should_calculate_count_correct(self):
        if 'count_correct' not in self.results or self.results['count_correct'] != 2:
            self.fail("compare_results should calculate the number of correct taggings")

    def test_should_calculate_count_incorrect(self):
        if 'count_incorrect' not in self.results or self.results['count_incorrect'] != 3:
            self.fail("compare_results should calculate the number of incorrect taggings")

    # TODO: Not a very intelligent test
    def test_should_calculate_percent_accuracy(self):
        if 'pct_accuracy' not in self.results or self.results['pct_accuracy'] != 0.4:
            self.fail("compare_results should calculate percent accuracy")


class TestAddLatCounts(TestCase):
    def setUp(self):
        text = """<AnnotatedText File="test.txt">
                <A LAT="LongRule1">two words</A>
                ,
                <A LAT="ShortRule1">now</A>
                <A LAT="ShortRule1">three</A>
                <A LAT="ShortRule2">words</A>
        </AnnotatedText>"""

        tags = CompareDocuscope.read_text(text)
        self.lats = CompareDocuscope.count_lats(tags)

    def test_should_return_structure_with_all_lats(self):
        lats = self.lats.keys()
        for lat in ['LongRule1', 'ShortRule1', 'ShortRule2']:
            if lat not in lats:
                self.fail("add_lat_counts should count all LATs")

    def test_should_return_structure_with_only_lats(self):
        lats = ['LongRule1', 'ShortRule1', 'ShortRule2']
        for lat in self.lats.keys():
            if lat not in lats:
                self.fail("add_lat_counts should only count LATs")

    def test_should_count_lats_correctly(self):
        correct_results = {
            'ShortRule1': 2,
            'ShortRule2': 1,
            'LongRule1': 1
        }
        for lat, count in self.lats.items():
            if count != correct_results[lat]:
                self.fail("add_lat_counts should count LATs properly")