import copy
from unittest import TestCase
import TestResults

__author__ = 'zthomae'


class TestArgumentParser(TestCase):
    def setUp(self):
        self.parser = TestResults.make_parser()

    def test_type_should_not_be_optional(self):
        try:
            TestResults.parse_args(self.parser, '--input foo --results bar'.split())
        except ValueError:
            return
        self.fail('Parser does not fail when a test type is not present')

    def test_inputs_should_not_be_optional(self):
        try:
            TestResults.parse_args(self.parser, '--type foo --results bar'.split())
        except ValueError:
            return
        self.fail('Parser does not fail when input files are not present')

    def test_results_should_not_be_optional(self):
        try:
            TestResults.parse_args(self.parser, '--type foo --input bar'.split())
        except ValueError:
            return
        self.fail('Parser does not fail when results files are not present')

    def test_only_one_type_allowed(self):
        try:
            TestResults.parse_args(self.parser, '--type two words --input foo --results bar'.split())
        except SystemExit:  # TODO: Wrap argparse behavior
            return
        self.fail('Parser accepts more than one test type')

    def test_should_expect_at_least_one_input_file(self):
        try:
            TestResults.parse_args(self.parser, '--type foo --input --results bar'.split())
        except SystemExit:
            return
        self.fail('Parser accepts zero input files')

    def test_should_expect_at_least_one_results_file(self):
        try:
            TestResults.parse_args(self.parser, '--type foo --input bar --results'.split())
        except SystemExit:
            return
        self.fail('Parser accepts zero results files')

    def test_should_allow_more_than_one_input_file(self):
        try:
            TestResults.parse_args(self.parser, '--type foo --input these files --results bar'.split())
        except SystemExit:
            self.fail("Parser doesn't accept multiple input files")

    def test_should_allow_more_than_one_results_file(self):
        try:
            TestResults.parse_args(self.parser, '--type foo --input file --results these files'.split())
        except SystemExit:
            self.fail("Parser doesn't accept multiple results files")


class TestInputFileParser(TestCase):
    def setUp(self):
        self.input_files = ['/foo/bar/Text1.txt', 'bar/baz/Text2.txt', 'Text3.txt', '../Text4.txt']
        self.results = TestResults.parse_input_files(self.input_files)

    def test_should_use_basename(self):
        if sorted(self.results.keys()) != sorted(['Text1.txt', 'Text2.txt', 'Text3.txt', 'Text4.txt']):
            self.fail('parse_input_files should return a dictionary with input file basenames as keys')

    def test_should_return_fullpaths(self):
        if any(map(lambda x: 'fullpath' not in x, self.results.values())):
            self.fail('parse_input_files should return fullpaths to input files')


class TestDocuscopeResultsParser(TestCase):
    def setUp(self):
        self.ds_results_file = ''.join([
            '<AnnotatedText File="Text1.txt" Group="foo" />',
            '<AnnotatedText File="Text2.txt" Group="foo" />',
            '<AnnotatedText File="Text3.txt" Group="bar" />'
        ])
        self.ds_results_file_2 = ''.join([
            '<AnnotatedText File="Text4.txt" Group="foo" />',
            '<AnnotatedText File="Text5.txt" Group="bar" />'
        ])
        self.ds_wrong_tag_results_file = ''.join([
            '<Text File="Text1.txt" Group="foo" />',
            '<Text File="Text2.txt" Group="foo" />',
            '<AnnotatedText File="Text3.txt" Group="foo" />'
        ])
        self.ds_wrong_attr_results_file = ''.join([
            '<AnnotatedText Fil="Text1.txt" Group="foo" />',
            '<AnnotatedText File="Text2.txt" Group="foo" />',
        ])

    def test_should_handle_one_file(self):
        results = TestResults.parse_docuscope_results([self.ds_results_file])
        keys = results.keys()
        if any([
            'Text1.txt' not in keys,
            'Text2.txt' not in keys,
            'Text3.txt' not in keys
        ]):
            self.fail("parse_docuscope_results didn't add expected files for one input file")

    def test_should_handle_multiples_files(self):
        results = TestResults.parse_docuscope_results([self.ds_results_file, self.ds_results_file_2])
        keys = results.keys()
        if any([
            'Text1.txt' not in keys,
            'Text2.txt' not in keys,
            'Text3.txt' not in keys,
            'Text4.txt' not in keys,
            'Text5.txt' not in keys
        ]):
            self.fail("parse_docuscope_results didn't add expected files for multiple input files")

    def test_should_not_add_files_in_wrong_element(self):
        results = TestResults.parse_docuscope_results([self.ds_wrong_tag_results_file])
        if len(results.keys()) > 1:
            self.fail('parse_docuscope_results added files not in AnnotatedText elements')

    def test_should_do_nothing_if_missing_file_attribute(self):
        results = TestResults.parse_docuscope_results([self.ds_wrong_attr_results_file])
        # TODO: Bad test
        if len(results.keys()) != 1:
            self.fail("parse_docuscope_results didn't add files correctly")

    def test_should_add_present_status(self):
        results = TestResults.parse_docuscope_results([self.ds_results_file])
        if any(map(lambda x: 'present' not in x, results.values())):
            self.fail('parse_docuscope_results should add "present" key')

    def test_should_add_text(self):
        results = TestResults.parse_docuscope_results([self.ds_results_file])
        # TODO: This test doesn't check as much as it should
        if any(map(lambda x: 'text' not in x, results.values())):
            self.fail('parse_docuscope_results should add "text" key')


class TestMatchFiles(TestCase):
    def setUp(self):
        self.results_files = {
            'Text1.txt': {'text': '', 'present': False},
            'Text2.txt': {'text': '', 'present': False},
            'Text3.txt': {'text': '', 'present': False}
        }

    def test_should_copy_results(self):
        if self.results_files != TestResults.match_files([], self.results_files):
            self.fail('match_files should return results_files if input_files empty')

    def test_should_set_file_true_if_in_inputs(self):
        files = TestResults.match_files(['Text1.txt'], self.results_files)
        if files['Text1.txt']['present'] is not True:
            self.fail('match_files should set entries to True if present in input_files')

    def test_should_keep_file_false_if_not_in_inputs(self):
        files = TestResults.match_files(['Text1.txt'], self.results_files)
        if any([
            files['Text2.txt']['present'] is not False,
            files['Text3.txt']['present'] is not False
        ]):
            self.fail('match_files should keep entries set to False if not present in input_files')

    def test_should_not_change_input_files(self):
        input_files = ['Text1.txt']
        old_input = copy.copy(input_files)
        TestResults.match_files(input_files, self.results_files)
        if old_input != input_files:
            self.fail('match_files should not change input_files')

    def test_should_not_change_results_files(self):
        old_results = copy.copy(self.results_files)
        TestResults.match_files(['Text1.txt'], self.results_files)
        if old_results != self.results_files:
            self.fail('match_files should not change results_files')


class TestComputeTestPairs(TestCase):
    def setUp(self):
        self.job = {
            'Text1.txt': {'text': 'first', 'present': True},
            'Text2.txt': {'text': 'second', 'present': False},
            'Text3.txt': {'text': 'third', 'present': True}
        }
        self.input_files = {
            'Text1.txt': {'fullpath': '/Text1.txt', 'text': ''},
            'Text2.txt': {'fullpath': '/Text2.txt', 'text': ''},
            'Text3.txt': {'fullpath': '/Text3.txt', 'text': ''},
        }
        self.results = TestResults.compute_test_pairs(self.job, self.input_files, self.format)

    @staticmethod
    def format(text):
        return text

    def test_should_throw_valueerror_if_too_few_input_files(self):
        input_files = copy.copy(self.input_files)
        del input_files['Text3.txt']
        try:
            TestResults.compute_test_pairs(self.job, input_files, self.format)
        except ValueError:
            return
        self.fail('compute_test_pairs should throw ValueError if an input file is not in input_files')

    def test_should_not_include_not_present_job_files(self):
        if 'Text2.txt' in self.results:
            self.fail('compute_test_pairs should not include texts if they are not "present" in the job')

    def test_should_not_check_if_non_present_input_files_are_missing(self):
        input_files = copy.copy(self.input_files)
        del input_files['Text2.txt']
        try:
            TestResults.compute_test_pairs(self.job, input_files, self.format)
        except ValueError:
            self.fail("compute_test_pairs shouldn't throw ValueError if non-present job file is not in input_files")

    def test_should_return_names(self):
        for v in self.results.values():
            if 'name' not in v:
                self.fail('compute_test_pairs should return text names')

    def test_should_return_ground_truths(self):
        for text in self.results:
            if self.results[text]['ground_truth'] != self.job[text]['text']:
                self.fail('compute_test_pairs should return ground_truth text')

    def test_should_return_formatted_input_file(self):
        for v in self.results.values():
            if 'test_input' not in v:
                self.fail('compute_test_pairs should return test_input')


class TestCompareTestPairs(TestCase):
    def setUp(self):
        self.test_pairs = {
            'Text1.txt': {
                'name': 'Text1.txt',
                'ground_truth': 'foo',
                'test_input': 'foo'
            },
            'Text2.txt': {
                'name': 'Text2.txt',
                'ground_truth': 'foo',
                'test_input': 'bar'
            }
        }
        self.results = TestResults.compare_test_pairs(self.test_pairs, self.compare)

    @staticmethod
    def compare(t1, t2):
        return {}

    def test_should_return_results_for_each_pair(self):
        if 'results' not in self.results['Text1.txt'] or 'results' not in self.results['Text2.txt']:
            self.fail('compare_test_pairs should return results for each of the test pairs')

    # TODO: Test more thoroughly