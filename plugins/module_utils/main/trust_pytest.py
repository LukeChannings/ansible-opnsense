from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust_ca import Ca
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust_cert import Cert


def test_trust_targets_the_model_controllers():
    assert Ca.API_MOD == 'trust'
    assert Ca.API_CONT == 'ca'
    assert Ca.API_KEY_PATH == 'ca'
    assert Cert.API_MOD == 'trust'
    assert Cert.API_CONT == 'cert'
    assert Cert.API_KEY_PATH == 'cert'


def test_trust_reloads_through_the_settings_controller():
    for cls in [Ca, Cert]:
        assert cls.API_CONT_REL == 'settings'


def test_trust_matches_entries_on_their_description():
    for cls in [Ca, Cert]:
        assert cls.FIELD_ID == 'description'
        assert cls.FIELDS_TRANSLATE['description'] == 'descr'


def test_trust_only_compares_the_key_material():
    # everything else the API returns is derived from the certificate
    for cls in [Ca, Cert]:
        assert cls.FIELDS_CHANGE == ['certificate', 'private_key']


def test_trust_sends_the_import_action_without_comparing_it():
    # the action never round-trips: a CA reads back as 'existing', a certificate
    # as 'reissue'/'manual' - and the models own default would re-generate
    for cls in [Ca, Cert]:
        assert 'action' in cls.FIELDS_ALL
        assert 'action' not in cls.FIELDS_CHANGE
        assert cls.FIELDS_DIFF_EXCLUDE == ['action']


def test_trust_writes_the_payload_fields():
    for cls in [Ca, Cert]:
        assert cls.FIELDS_TRANSLATE['certificate'] == 'crt_payload'
        assert cls.FIELDS_TRANSLATE['private_key'] == 'prv_payload'


def test_trust_keeps_the_private_key_out_of_the_diff():
    for cls in [Ca, Cert]:
        assert cls.FIELDS_DIFF_NO_LOG == ['private_key']


def test_trust_still_compares_the_private_key():
    # excluded from the diff-output, but not from change-detection
    for cls in [Ca, Cert]:
        assert 'private_key' in cls.FIELDS_CHANGE


def test_trust_redacts_the_raw_private_key_field_too():
    # the API returns the key twice: base64 as 'prv' and PEM as 'prv_payload'
    for cls in [Ca, Cert]:
        no_log = cls._api_no_log_fields()
        assert 'private_key' in no_log
        assert 'prv_payload' in no_log
        assert 'prv' in no_log
