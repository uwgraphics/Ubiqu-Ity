from unittest import TestCase
from Ity.Taggers import Tagger
from Ity.Tokenizers import Tokenizer

__author__ = 'zthomae'


class StubTagger(Tagger):
    def tag(self, rules):
        return {}, []


class TestConstructor(TestCase):
    def setUp(self):
        return

    def test_should_begin_full_label_with_excluded_token_types(self):
        excluded_token_types = (1, 2, 3)
        tagger = StubTagger(excluded_token_types=excluded_token_types)
        if not tagger._full_label.startswith(str(excluded_token_types)):
            self.fail("_full_label should begin with excluded token types tuple as string")

    def test_should_follow_excluded_token_types_with_period(self):
        excluded_token_types = (1, 2, 3)
        tagger = StubTagger(excluded_token_types=excluded_token_types)
        dot_index = tagger._full_label.index(str(excluded_token_types)) + len(str(excluded_token_types))
        if tagger._full_label[dot_index] != '.':
            self.fail("_full_label should insert a '.' after excluded token types")

    def test_should_follow_first_dot_with_case_sensitive(self):
        excluded_token_types = (1, 2, 3)
        case_sensitive = False
        tagger = StubTagger(excluded_token_types=excluded_token_types, case_sensitive=case_sensitive)
        dot_index = tagger._full_label.index(str(excluded_token_types)) + len(str(excluded_token_types))
        if not tagger._full_label[dot_index+1:].startswith(str(case_sensitive)):
            self.fail("_full_label should follow '.' after excluded token types with case_sensitive")

    def test_should_follow_case_sensitive_with_dot(self):
        excluded_token_types = (1, 2, 3)
        case_sensitive = False
        tagger = StubTagger(excluded_token_types=excluded_token_types, case_sensitive=case_sensitive)
        first_dot_index = tagger._full_label.index(str(excluded_token_types)) + len(str(excluded_token_types))
        second_dot_index = first_dot_index + len(str(case_sensitive)) + 1
        if not tagger._full_label[second_dot_index:].startswith('.'):
            self.fail("_full_label should have '.' after case_sensitive")

    def test_should_follow_second_dot_with_excl(self):
        excluded_token_types = (1, 2, 3)
        case_sensitive = False
        tagger = StubTagger(excluded_token_types=excluded_token_types, case_sensitive=case_sensitive)
        first_dot_index = tagger._full_label.index(str(excluded_token_types)) + len(str(excluded_token_types))
        second_dot_index = first_dot_index + len(str(case_sensitive)) + 1
        if not tagger._full_label[second_dot_index+1:].startswith('EXCL_'):
            self.fail("_full_label should have 'EXCL_' after '.' following case_sensitive")

    def test_should_follow_excl_with_excluded_meta_rule_names(self):
        self.tagger = StubTagger(untagged_rule_name='UNTAGGED',
                                 no_rules_rule_name='NORULES',
                                 excluded_rule_name='EXCLUDED')
        meta_rules_index = self.tagger._full_label.index('EXCL_')
        meta_rules_string = '.'.join(['EXCL_' + meta_rule_name
                                      for meta_rule_name in self.tagger.excluded_meta_rule_names])
        if not self.tagger._full_label[meta_rules_index:] == meta_rules_string:
            self.fail('_full_label should end with dot-separated string of EXCL_<rule>s for excluded meta rule names')


class TestMetaRuleNamesProperty(TestCase):
    def setUp(self):
        self.tagger = StubTagger()
        self.tagger.untagged_rule_name = 'UNTAGGED'
        self.tagger.no_rules_rule_name = 'NORULES'
        self.tagger.excluded_rule_name = 'EXCLUDED'

    def test_should_return_untagged_no_rules_and_excluded(self):
        meta_rule_names = self.tagger.meta_rule_names
        if any([
            self.tagger.untagged_rule_name not in meta_rule_names,
            self.tagger.no_rules_rule_name not in meta_rule_names,
            self.tagger.excluded_rule_name not in meta_rule_names,
        ]):
            self.fail("meta_rule_names should include untagged, no rules, and excluded rule names")


class TestExcludedMetaRuleNamesProperty(TestCase):
    def setUp(self):
        self.tagger = StubTagger()
        self.tagger.untagged_rule_name = 'UNTAGGED'
        self.tagger.no_rules_rule_name = 'NORULES'
        self.tagger.excluded_rule_name = 'EXCLUDED'
        self.tagger.return_untagged_tags = False
        self.tagger.return_no_rules_tags = False
        self.tagger.return_excluded_tags = False

    def test_should_add_untagged_if_to_return(self):
        self.tagger.return_untagged_tags = True
        if self.tagger.untagged_rule_name in self.tagger.excluded_meta_rule_names:
            self.fail("excluded_meta_rule_names shouldn't add untagged_rule_name if return_untagged_tags is True")

    def test_should_not_add_untagged_if_not_to_return(self):
        if self.tagger.untagged_rule_name not in self.tagger.excluded_meta_rule_names:
            self.fail("excluded_meta_rule_names should add untagged_rule_name if return_untagged_tags is False")

    def test_should_add_no_rules_if_to_return(self):
        self.tagger.return_no_rules_tags = True
        if self.tagger.no_rules_rule_name in self.tagger.excluded_meta_rule_names:
            self.fail("excluded_meta_rule_names shouldn't add no_rules_rule_name if return_no_rules_tags is True")

    def test_should_not_add_no_rules_if_not_to_return(self):
        if self.tagger.no_rules_rule_name not in self.tagger.excluded_meta_rule_names:
            self.fail("excluded_meta_rule_names should add no_rules_rule_name if return_no_rules_tags is False")

    def test_should_add_excluded_if_to_return(self):
        self.tagger.return_excluded_tags = True
        if self.tagger.excluded_rule_name in self.tagger.excluded_meta_rule_names:
            self.fail("excluded_meta_rule_names shouldn't add excluded_rule_name if return_excluded_tags is True")

    def test_should_not_add_excluded_if_not_to_return(self):
        if self.tagger.excluded_rule_name not in self.tagger.excluded_meta_rule_names:
            self.fail("excluded_meta_rule_names should add excluded_rule_name if return_excluded_tags is False")

    def test_should_add_all_types_to_be_excluded(self):
        excluded_meta_rule_names = self.tagger.excluded_meta_rule_names
        if not all([
            self.tagger.untagged_rule_name in excluded_meta_rule_names,
            self.tagger.no_rules_rule_name in excluded_meta_rule_names,
            self.tagger.excluded_rule_name in excluded_meta_rule_names,
        ]):
            self.fail("excluded_meta_rule_names should add all tag names that aren't supposed to be returned")

    def test_should_allow_no_tags_to_be_excluded(self):
        self.tagger.return_untagged_tags = True
        self.tagger.return_no_rules_tags = True
        self.tagger.return_excluded_tags = True
        excluded_meta_rule_names = self.tagger.excluded_meta_rule_names
        if len(excluded_meta_rule_names) > 0:
            self.fail("excluded_meta_rule_names should allow no tags to be excluded by returning an empty list")


class TestShouldReturnRule(TestCase):
    def setUp(self):
        self.tagger = StubTagger()
        self.tagger.untagged_rule_name = 'UNTAGGED'
        self.tagger.no_rules_rule_name = 'NORULES'
        self.tagger.excluded_rule_name = 'EXCLUDED'
        self.tagger.return_untagged_tags = False
        self.tagger.return_no_rules_tags = False
        self.tagger.return_excluded_tags = False
        self.rule = {'name': 'INCLUDED'}

    def test_should_check_excluded_meta_rule_names(self):
        self.rule['name'] = self.tagger.untagged_rule_name
        if self.tagger._should_return_rule(self.rule):
            self.fail("_should_return_rule should check excluded_meta_rule_names")

    def test_should_check_return_included_tags(self):
        self.tagger.return_included_tags = False
        if self.tagger._should_return_rule(self.rule):
            self.fail("_should_return_rule should check return_included_tags")

    def test_meta_rule_names_and_no_return_included_tags(self):
        self.tagger.return_included_tags = False
        # Change rule name to something in meta_rule_names...
        self.rule['name'] = self.tagger.no_rules_rule_name
        # ...and take that out of excluded_meta_rule_names
        self.tagger.return_no_rules_tags = True
        if not self.tagger._should_return_rule(self.rule):
            self.fail("_should_return_rule should check if the rule is a non-excluded meta rule if "
                      "return_included_tags is False")


class TestValidRules(TestCase):
    def setUp(self):
        self.tagger = StubTagger()
        self.rule = {'name': 'fake', 'full_name': self.tagger.full_label + 'FakeRule',
                     'num_tags': 1, 'num_included_tokens': 1}

    def test_valid_rule(self):
        if not self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule doesn't consider a valid rule valid")

    def test_empty_rule_invalid(self):
        if self.tagger._is_valid_rule(Tagger.empty_rule):
            self.fail("_is_valid_rule considers Tagger.empty_rule valid")

    def test_empty_dict_invalid(self):
        self.rule = {}
        if self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule considers an empty dict valid")

    def test_empty_dict_no_exceptions(self):
        self.rule = {}
        try:
            self.tagger._is_valid_rule(self.rule)
        except:
            self.fail("_is_valid_rule throws an exception with an empty dict")

    def test_rule_missing_name_invalid(self):
        del self.rule['name']
        if self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule validates without 'name'")

    def test_rule_missing_name_no_exceptions(self):
        del self.rule['name']
        try:
            self.tagger._is_valid_rule(self.rule)
        except:
            self.fail("_is_valid_rule throws an exception when missing 'name'")

    def test_rule_missing_full_name_invalid(self):
        del self.rule['full_name']
        if self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule validates without 'full_name'")

    def test_rule_missing_full_name_no_exceptions(self):
        del self.rule['full_name']
        try:
            self.tagger._is_valid_rule(self.rule)
        except:
            self.fail("_is_valid_rule throws an exception when missing 'full_name'")

    def test_rule_missing_num_tags_invalid(self):
        del self.rule['num_tags']
        if self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule validates without 'num_tags'")

    def test_rule_missing_num_tags_no_exceptions(self):
        del self.rule['num_tags']
        try:
            self.tagger._is_valid_rule(self.rule)
        except:
            self.fail("_is_valid_rule throws an exception when missing 'num_tags'")

    def test_rule_missing_num_included_tokens_invalid(self):
        del self.rule['num_included_tokens']
        if self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule validates without 'num_included_tokens'")

    def test_rule_missing_num_included_tokens_no_exceptions(self):
        del self.rule['num_included_tokens']
        try:
            self.tagger._is_valid_rule(self.rule)
        except:
            self.fail("_is_valid_rule throws an exception when missing 'num_included_tokens'")

    def test_rule_missing_full_label_invalid(self):
        self.rule['full_name'] = 'FakeRule'
        if self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule validates when 'full_name' doesn't start with full label")

    def test_num_tags_allow_zero(self):
        self.rule['num_tags'] = 0
        if not self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule validates when 'num_tags' == 0")

    def test_num_included_tokens_allow_zero(self):
        self.rule['num_included_tokens'] = 0
        if not self.tagger._is_valid_rule(self.rule):
            self.fail("_is_valid_rule validates when 'num_included_tokens' == 0")


class TestValidTags(TestCase):
    def setUp(self):
        self.tagger = StubTagger()
        self.tagger.tokens = [('one', 'two') for i in range(0, 7)]
        self.tag = {'rules': [('one', 'two')], 'index_start': 1, 'index_end': 5, 'len': 1,
                    'pos_start': 1, 'pos_end': 2, 'token_end_len': 1}

    def test_valid_tag(self):
        if not self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't consider a valid tag to be valid")

    def test_empty_tag_invalid(self):
        if self.tagger._is_valid_tag(Tagger.empty_tag):
            self.fail("_is_valid_tag considers Tagger.empty_tag to be valid")

    def test_non_tuples_rules_invalid(self):
        self.tag['rules'] = [0]
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't check if 'rules' filled with tuples")

    def test_too_small_size_rules_invalid(self):
        self.tag['rules'].append(('one'))
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't check if 'rules' tuples are too small")

    def test_too_big_size_rules_invalid(self):
        self.tag['rules'].append(('one', 'two', 'three'))
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't check if 'rules' tuples are too big")

    def test_index_start_zero_valid(self):
        self.tag['index_start'] = 0
        if not self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't allow 'index_start' to be 0")

    def test_index_start_negative_invalid(self):
        self.tag['index_start'] = -1
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag allows 'index_start' to be negative")

    def test_index_end_last_token_valid(self):
        self.tag['index_end'] = len(self.tagger.tokens) - 1
        if not self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't allow 'index_end' to be the last token")

    def test_index_end_after_last_token_invalid(self):
        self.tag['index_end'] = len(self.tagger.tokens) + 1
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag allows 'index_end' to be after the last token")

    def test_index_end_off_by_one_invalid(self):
        self.tag['index_end'] = len(self.tagger.tokens)
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag has an off-by-one error in testing the length of self.tokens")

    def test_index_start_equals_index_end_valid(self):
        self.tag['index_start'] = self.tag['index_end']
        if not self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't allow 'index_start' to equal 'index_end'")

    def test_len_zero_invalid(self):
        self.tag['len'] = 0
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag allows 'len' to be 0")

    def test_pos_start_zero_valid(self):
        self.tag['pos_start'] = 0
        if not self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't allow 'pos_start' to be 0")

    def test_pos_start_negative_invalid(self):
        self.tag['pos_start'] = -1
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag allows 'pos_start' to be negative")

    def test_pos_end_zero_valid(self):
        # Need to set pos_start to 0 so pos_start <= pos_end is True
        self.tag['pos_start'] = 0
        self.tag['pos_end'] = 0
        if not self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't allow 'pos_end' to be 0")

    def test_pos_end_negative_invalid(self):
        self.tag['pos_end'] = -1
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag allows 'pos_end' to be negative")

    def test_pos_start_equals_pos_end_valid(self):
        self.tag['pos_start'] = self.tag['pos_end']
        if not self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag doesn't allow 'pos_start' to equal 'pos_end'")

    def test_token_end_len_zero_invalid(self):
        self.tag['token_end_len'] = 0
        if self.tagger._is_valid_tag(self.tag):
            self.fail("_is_valid_tag allows 'token_end_len' to be 0")


class TestGetNthNextIncludedTokenIndex(TestCase):
    def setUp(self):
        self.tagger = StubTagger(excluded_token_types=(Tokenizer.TYPES['WHITESPACE'],))
        self.tagger.tokens = [{Tokenizer.INDEXES['TYPE']: Tokenizer.TYPES['WORD']} for i in range(0, 10)]
        self.tagger.token_index = 3

    def test_should_use_token_index_as_default(self):
        if self.tagger._get_nth_next_included_token_index() != self.tagger.token_index + 1:
            self.fail("_get_nth_next_included_token_index should use token_index as a default starting token index")

    def test_should_accept_starting_token_index_argument(self):
        if self.tagger._get_nth_next_included_token_index(starting_token_index=0) != 1:
            self.fail("_get_nth_next_included_token_index should accept optional starting_token_index argument")

    def test_should_use_default_n_value_of_one(self):
        # This is literally the same test...
        if self.tagger._get_nth_next_included_token_index() != self.tagger.token_index + 1:
            self.fail("_get_nth_next_included_token_index should use 1 as a default n value")

    def test_should_accept_n_argument(self):
        if self.tagger._get_nth_next_included_token_index(n=2) != self.tagger.token_index + 2:
            self.fail("_get_nth_next_included_token_index should accept optional n argument")

    def test_should_return_none_if_after_end_of_tokens(self):
        if self.tagger._get_nth_next_included_token_index(n=len(self.tagger.tokens) + 1) is not None:
            self.fail("_get_nth_next_included_token_index should return None if past the end of the tokens list")

    def test_should_reach_last_token(self):
        token_index = self.tagger._get_nth_next_included_token_index(starting_token_index=0,
                                                                     n=len(self.tagger.tokens) - 1)
        if token_index != len(self.tagger.tokens) - 1:
            self.fail("_get_nth_next_included_token_index should be able to return last token index "
                      "(there may be an off-by-one error here)")

    def test_should_not_change_tagger_state(self):
        last_index = self.tagger._get_nth_next_included_token_index()
        if last_index != self.tagger._get_nth_next_included_token_index():
            self.fail("_get_nth_next_included_token_index should return the same results on all calls if "
                      "there are no changes in the state of the Tagger")

    def test_should_skip_excluded_tokens(self):
        self.tagger.tokens[self.tagger.token_index + 1][Tokenizer.INDEXES['TYPE']] = Tokenizer.TYPES['WHITESPACE']
        if self.tagger._get_nth_next_included_token_index(n=1) != self.tagger.token_index + 2:
            self.fail("_get_nth_next_included_token_index should not return index of excluded token")