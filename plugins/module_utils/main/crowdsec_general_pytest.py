from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.crowdsec_general import General


def test_crowdsec_general_targets_the_general_settings_object():
    assert General.API_MOD == 'crowdsec'
    assert General.API_CONT == 'general'
    assert General.API_KEY_PATH == 'general'
    assert General.API_KEY_PATH_REQ == General.API_KEY_PATH


def test_crowdsec_general_manages_every_model_field():
    assert General.FIELDS_CHANGE == [
        'agent_enabled', 'lapi_enabled', 'firewall_bouncer_enabled',
        'lapi_manual_configuration', 'lapi_listen_address', 'lapi_listen_port',
        'rules_enabled', 'rules_log', 'rules_tag', 'enroll_key',
        'crowdsec_firewall_verbose',
    ]
    assert General.FIELDS_ALL == General.FIELDS_CHANGE


def test_crowdsec_general_toggles_are_booleans():
    for field in [
        'agent_enabled', 'lapi_enabled', 'firewall_bouncer_enabled',
        'lapi_manual_configuration', 'rules_enabled', 'rules_log',
        'crowdsec_firewall_verbose',
    ]:
        assert field in General.FIELDS_TYPING['bool']


def test_crowdsec_general_lapi_port_is_a_validated_int():
    assert General.FIELDS_TYPING['int'] == ['lapi_listen_port']
    assert General.INT_VALIDATIONS['lapi_listen_port'] == {'min': 1, 'max': 65535}


def test_crowdsec_general_keeps_the_enroll_key_out_of_the_diff():
    assert General.FIELDS_DIFF_NO_LOG == ['enroll_key']


def test_crowdsec_general_still_compares_the_enroll_key():
    # excluded from the diff-output, but not from change-detection
    assert 'enroll_key' in General.FIELDS_CHANGE
