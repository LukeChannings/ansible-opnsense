def test_placeholder():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.logic import BaseLogic


def test_api_no_log_fields_is_empty_without_no_log_fields():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.logic import BaseLogic

    assert BaseLogic._api_no_log_fields() == []


def test_api_no_log_fields_covers_the_translated_field_names():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.logic import BaseLogic

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
