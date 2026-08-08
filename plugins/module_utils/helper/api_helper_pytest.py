def test_placeholder():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.api import \
        _load_credential_file, check_or_load_credentials, check_host, ssl_verification, \
        get_params_path, _clean_response, debug_api, check_response, api_pretty_exception


def test_redact_data_masks_no_log_fields_at_any_depth():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.api import \
        _redact_data, VALUE_NO_LOG

    assert _redact_data(
        {'general': {'enroll_key': 'supersecret', 'rules_tag': 'crowdsec'}},
        ['enroll_key'],
    ) == {'general': {'enroll_key': VALUE_NO_LOG, 'rules_tag': 'crowdsec'}}


def test_redact_data_leaves_unlisted_fields_alone():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.api import _redact_data

    data = {'general': {'enroll_key': 'supersecret'}}
    assert _redact_data(data, []) == data


def test_redact_content_masks_no_log_fields_in_a_response_body():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.api import \
        _redact_content, VALUE_NO_LOG

    assert _redact_content(
        b'{"general":{"enroll_key":"supersecret","rules_tag":"crowdsec"}}',
        ['enroll_key'],
    ) == b'{"general":{"enroll_key":"' + VALUE_NO_LOG.encode() + b'","rules_tag":"crowdsec"}}'


def test_clean_response_masks_no_log_fields():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.api import \
        _clean_response, VALUE_NO_LOG

    cleaned = _clean_response(
        {'status_code': 200, '_content': b'{"general":{"enroll_key":"supersecret"}}', 'headers': {}},
        ['enroll_key'],
    )

    assert b'supersecret' not in cleaned['_content']
    assert VALUE_NO_LOG.encode() in cleaned['_content']
    assert 'headers' not in cleaned
