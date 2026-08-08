from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.logic import BaseLogic
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
    MockAnsibleModule


class DummySearchLogic(BaseLogic):
    CMDS = {
        'search': 'search_rule',
        'detail': 'get_rule',
    }
    API_KEY_PATH = 'rule'
    API_MOD = 'firewall'
    API_CONT = 'source_nat'
    FIELDS_ALL = []
    FIELDS_CHANGE = []
    FIELDS_TYPING = {}

    def check(self) -> None:
        return


def test_search_skips_detail_lookup_for_automatic_entries(mocker):
    module = MockAnsibleModule()
    module.params.update({
        'description': 'automatic_isakmp_wan',
    })
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    logic = DummySearchLogic(module, result)
    setattr(logic, BaseLogic.ATTR_SKIP_AUTO_ENTRIES, True)

    automatic_entry = {
        'uuid': 'auto-rule-1',
        'description': 'automatic_isakmp_wan',
        'is_automatic': True,
    }

    mocker.patch.object(logic, 'api_search_post', return_value=[automatic_entry])
    mocker.patch.object(logic, '_api_get')

    entries = logic.search(match_fields=['description'])

    assert entries == []


def test_api_no_log_fields_is_empty_without_no_log_fields():
    assert BaseLogic._api_no_log_fields() == []


def test_api_no_log_fields_covers_the_translated_field_names():
    class _Flat(BaseLogic):
        FIELDS_DIFF_NO_LOG = ['enroll_key']

    class _Translated(BaseLogic):
        FIELDS_DIFF_NO_LOG = ['private_key']
        FIELDS_TRANSLATE = {'private_key': 'privkey'}

    class _Nested(BaseLogic):
        FIELDS_DIFF_NO_LOG = ['auth_password']
        FIELDS_TRANSLATE = {'auth_password': ('auth', 'password')}

    assert _Flat._api_no_log_fields() == ['enroll_key']
    assert _Translated._api_no_log_fields() == ['private_key', 'privkey']
    assert _Nested._api_no_log_fields() == ['auth_password', 'password']
