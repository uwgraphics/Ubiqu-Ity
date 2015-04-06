from unittest import TestCase
from Ity.Formatters.HTMLFormatter import HTMLFormatter

__author__ = 'zthomae'


class TestPrepareTokens(TestCase):
    def setUp(self):
        self.formatter = HTMLFormatter()
        self.text = "So shaken as we are, so wan with care"
        self.tokens = [
            [['So'], 0, 2, 0],
            [[' '], 2, 1, 2],
            [['shaken'], 3, 6, 0],
            [[' '], 9, 1, 2],
            [['as'], 10, 2, 0],
            [[' '], 12, 1, 2],
            [['we'], 13, 2, 0],
            [[' '], 15, 1, 2],
            [['are'], 16, 3, 0],
            [[','], 19, 1, 1],
            [[' '], 20, 1, 2],
            [['so'], 21, 2, 0],
            [[' '], 23, 1, 2],
            [['wan'], 24, 3, 0],
            [[' '], 27, 1, 2],
            [['with'], 28, 4, 0],
            [[' '], 32, 1, 2],
            [['care'], 33, 4, 0]
        ]
        self.tags = [None, [
            {'index_end': 2, 'rules': [(
                                        'DocuscopeTagger..default.(2, 3).True.EXCL_!UNTAGGED.EXCL_!NORULES.EXCL_!EXCLUDED.Transformation',
                                        'shaken')],
              'token_end_len': 6, 'len': 1, 'num_included_tokens': 1,
              'index_start': 2, 'pos_end': 3, 'pos_start': 3},
             {'index_end': 8, 'rules': [(
                                        'DocuscopeTagger..default.(2, 3).True.EXCL_!UNTAGGED.EXCL_!NORULES.EXCL_!EXCLUDED.ReportingStates',
                                        ('we', 'are'))],
              'token_end_len': 3, 'len': 1, 'num_included_tokens': 2,
              'index_start': 6, 'pos_end': 16, 'pos_start': 13},
             {'index_end': 11, 'rules': [(
                                         'DocuscopeTagger..default.(2, 3).True.EXCL_!UNTAGGED.EXCL_!NORULES.EXCL_!EXCLUDED.ReasonForward',
                                         (',', 'so'))],
              'token_end_len': 2, 'len': 1, 'num_included_tokens': 2,
              'index_start': 9, 'pos_end': 21, 'pos_start': 19},
             {'index_end': 13, 'rules': [(
                                         'DocuscopeTagger..default.(2, 3).True.EXCL_!UNTAGGED.EXCL_!NORULES.EXCL_!EXCLUDED.Negativity',
                                         'wan')],
              'token_end_len': 3, 'len': 1, 'num_included_tokens': 1,
              'index_start': 13, 'pos_end': 24, 'pos_start': 24},
             {'index_end': 17, 'rules': [(
                                         'DocuscopeTagger..default.(2, 3).True.EXCL_!UNTAGGED.EXCL_!NORULES.EXCL_!EXCLUDED.StandardsPos',
                                         ('with', 'care'))],
              'token_end_len': 4, 'len': 1, 'num_included_tokens': 2,
              'index_start': 15, 'pos_end': 33, 'pos_start': 28}
        ]]
        self.prepared_tokens = self.formatter.prepare_tokens(tokens=self.tokens, tags=self.tags)
        self.tag_map = {
            1: 'Transformation',
            3: 'ReportingStates',
            4: 'ReasonForward',
            6: 'Negativity',
            8: 'StandardsPos'
        }
        self.pos_map = {
            0: 0,
            1: 3,
            2: 9,
            3: 13,
            4: 19,
            5: 23,
            6: 24,
            7: 27,
            8: 28
        }

    def test_should_include_entire_text(self):
        new_text = ''.join([t['text'] for t in self.prepared_tokens])
        if not new_text == self.text:
            self.fail('prepare_tokens result should contain the entire text')

    def test_should_include_all_tags(self):
        for i, t in enumerate(self.prepared_tokens):
            if i not in self.tag_map:
                continue
            if self.tag_map[i] not in t['tag']:
                self.fail('prepare_tokens result should contain all tags')

    def test_should_make_untagged_tokens_none(self):
        for i, t in enumerate(self.prepared_tokens):
            if i in self.tag_map:
                continue
            if t['tag'] is not None:
                self.fail('prepare_tokens result should contain None for untagged tokens')

    def test_should_trim_tag_names(self):
        for i, t in enumerate(self.prepared_tokens):
            if i not in self.tag_map:
                continue
            if '.' in t['tag']:
                self.fail('prepare_tokens should trim tag names (i.e. have no .s in it)')

    def test_should_include_pos_start(self):
        for i, t in enumerate(self.prepared_tokens):
            if 'pos_start' not in t or t['pos_start'] != self.pos_map[i]:
                self.fail('prepare_tokens should include pos_start for each token')


class TestPaginate(TestCase):
    def setUp(self):
        self.pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.page_size = 3
        self.formatter = HTMLFormatter()
        self.paginated = self.formatter.paginate(self.pages, self.page_size)

    def test_all_items_should_be_in_pages(self):
        pages = []
        for p in self.paginated:
            for pi in p:
                pages.append(pi)
        if pages != self.pages:
            self.fail('paginate should return all items in order')

    def test_all_but_last_entry_should_be_page_size_long(self):
        for p in self.paginated[:-1]:
            if len(p) != self.page_size:
                self.fail('all but the last page result from paginate should be of length equal to the page size')

    def test_last_entry_should_be_up_to_page_size_long(self):
        if len(self.paginated[-1]) > self.page_size:
            self.fail('last result from paginate should be less than or equal to the page size in length')


class TestPrepareTags(TestCase):
    def setUp(self):
        self.tags = {
            'key1': {'name': '1', 'full_name': 'key1'},
            'key2': {'name': '2', 'full_name': 'key2'},
            'key3': {'name': '3', 'full_name': 'key3'}
        }
        self.formatter = HTMLFormatter()
        self.prepared_tags = self.formatter.prepare_tags(self.tags)

    def test_all_dicts_present(self):
        for v in self.prepared_tags.values():
            if v not in self.tags.values():
                self.fail('prepare_tags should include all inner dict values')

    def test_names_are_keys(self):
        for k, v in self.prepared_tags.items():
            if k != v['name']:
                self.fail('prepare_tags should use "name" members as keys')