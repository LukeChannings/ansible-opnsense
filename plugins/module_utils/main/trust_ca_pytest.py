import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
    pytest_mock_http_responses, MockAnsibleModule, AnsibleError
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.trust_ca_testdata import \
    Testdata_26_7_3 as CaTestdata, SECRET

PARAMS = dict(
    description='TestCA', ca='', key_type='2048', digest='sha256', lifetime=825, common_name='OPNsense Test CA',
    country='AT', state_or_province='', city='', organization='', organizational_unit='', email='', ocsp_uri='',
    match_fields=['description'], state='present',
)
PARAMS_OPENVPN = {**PARAMS, 'description': 'OpenVPN', 'common_name': 'openvpn'}


def _mock(mocker) -> CaTestdata:
    testdata = CaTestdata()
    pytest_mock_http_responses(mocker=mocker, handler=testdata)
    return testdata


def _run(params: dict, check_mode: bool = False) -> dict:
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust_ca import Ca

    module = MockAnsibleModule()
    module.params.update(params)
    module.check_mode = check_mode
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    module_wrapper(Ca(module=module, result=result))
    assert SECRET not in str(result)
    return result


def test_trust_ca_create_and_rerun(mocker):
    testdata = _mock(mocker)
    params = {**PARAMS, 'lifetime': 36500, 'key_type': 'secp521r1'}

    result = _run(params)
    assert result['changed']
    assert len(testdata.mutations()) == 1
    request = testdata.mutations()[0][1]
    assert request['action'] == 'internal'
    assert request['descr'] == 'TestCA'
    assert request['caref'] == ''
    assert request['commonname'] == 'OPNsense Test CA'
    assert request['key_type'] == 'secp521r1'
    assert request['lifetime'] == 36500

    # the API returns the default lifetime - the actual one must be calculated from the validity-timestamps
    result = _run(params)
    assert not result['changed']
    assert len(testdata.mutations()) == 1


def test_trust_ca_check_mode(mocker):
    testdata = _mock(mocker)
    result = _run(PARAMS, check_mode=True)
    assert result['changed']
    assert len(testdata.mutations()) == 0


@pytest.mark.parametrize('changed', [
    {'key_type': '4096'},
    {'lifetime': 3650},
    {'common_name': 'other'},
    {'country': 'DE'},
    {'ca': 'OpenVPN'},
])
def test_trust_ca_immutable(mocker, changed: dict):
    testdata = _mock(mocker)
    _run(PARAMS)

    with pytest.raises(AnsibleError, match='cannot be changed without re-issuing'):
        _run({**PARAMS, **changed})

    assert len(testdata.mutations()) == 1


def test_trust_ca_rename_keeps_ca(mocker):
    testdata = _mock(mocker)
    _run(PARAMS)

    params = {**PARAMS, 'description': 'TestCA renamed', 'match_fields': ['common_name']}
    result = _run(params)
    assert result['changed']
    assert result['diff']['before']['description'] == 'TestCA'
    assert result['diff']['after']['description'] == 'TestCA renamed'

    request = testdata.mutations()[-1][1]
    assert request['action'] == 'existing'
    assert request['descr'] == 'TestCA renamed'
    assert request['crt_payload'] != ''
    assert len(testdata.regenerated) == 0

    assert not _run(params)['changed']


def test_trust_ca_intermediate(mocker):
    testdata = _mock(mocker)
    _run({**PARAMS, 'ca': 'OpenVPN'})
    assert testdata.mutations()[-1][1]['caref'] == '65f0af2ce06c7'

    # matching by reference-id
    assert not _run({**PARAMS, 'ca': '65f0af2ce06c7'})['changed']

    with pytest.raises(AnsibleError, match='was not found'):
        _run({**PARAMS, 'description': 'other', 'ca': 'does-not-exist'})


def test_trust_ca_delete(mocker):
    testdata = _mock(mocker)
    _run(PARAMS)

    result = _run({**PARAMS, 'state': 'absent'})
    assert result['changed']
    assert testdata.mutations()[-1][0] == 'del'

    assert not _run({**PARAMS, 'state': 'absent'})['changed']


def test_trust_ca_delete_in_use(mocker):
    testdata = _mock(mocker)
    with pytest.raises(AnsibleError, match='still referenced'):
        _run({**PARAMS_OPENVPN, 'state': 'absent'})

    assert len(testdata.mutations()) == 0


def test_trust_ca_ambiguous(mocker):
    testdata = _mock(mocker)
    _run(PARAMS)
    _run({**PARAMS, 'description': 'TestCA 2'})

    with pytest.raises(AnsibleError, match='Multiple existing'):
        _run({**PARAMS, 'match_fields': ['common_name']})


def test_trust_ca_existing_has_no_secrets(mocker):
    _mock(mocker)

    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust_ca import Ca

    module = MockAnsibleModule()
    module.params.update(PARAMS)
    existing = Ca(module=module, result={}).get_existing()
    assert len(existing) == 1
    assert existing[0]['description'] == 'OpenVPN'
    assert existing[0]['lifetime'] == 825
    assert existing[0]['crt_payload'].startswith('-----BEGIN CERTIFICATE-----')
    assert SECRET not in str(existing)

    # used by the 'list' module
    raw = Ca(module=module, result={}).search_call()
    assert len(raw) == 1
    assert raw[0]['descr'] == 'OpenVPN'
    assert SECRET not in str(raw)


# --- importing an externally-issued CA ----------------------------------------
# OPNsense's trust-API takes an existing certificate via action='existing' with a
# 'crt_payload'. Without this the module can only ever generate an internal CA,
# so a fleet CA issued elsewhere cannot be placed in the firewall's trust store.

def _pem(body: str, kind: str = 'CERTIFICATE') -> str:
    from base64 import b64encode
    return f"-----BEGIN {kind}-----\n{b64encode(body.encode()).decode()}\n-----END {kind}-----\n"


ROOT_CA_PEM = _pem('hartland-root-ca-der')
ROTATED_CA_PEM = _pem('hartland-root-ca-der-v2')
ROOT_CA_KEY = _pem('hartland-root-ca-key', kind='PRIVATE KEY')

PARAMS_IMPORT = {
    **PARAMS,
    'description': 'Hartland CA',
    'certificate': ROOT_CA_PEM,
    'private_key': None,
}


def test_trust_ca_import_sends_the_certificate_instead_of_generating(mocker):
    testdata = _mock(mocker)

    result = _run(PARAMS_IMPORT)

    assert result['changed']
    assert len(testdata.mutations()) == 1
    kind, request = testdata.mutations()[0]
    assert kind == 'add'
    assert request['action'] == 'existing'
    assert request['crt_payload'] == ROOT_CA_PEM
    assert request['descr'] == 'Hartland CA'
    # nothing was issued - the imported payload survived
    assert testdata.regenerated == []


def test_trust_ca_import_is_idempotent(mocker):
    testdata = _mock(mocker)
    _run(PARAMS_IMPORT)

    result = _run(PARAMS_IMPORT)

    assert not result['changed']
    assert len(testdata.mutations()) == 1


def test_trust_ca_import_does_not_trip_the_immutable_check(mocker):
    # the subject, key-type, digest and validity all come from the certificate -
    # the generation-parameters were never used, so their defaults must not be
    # compared against what the API parsed out of the imported certificate
    _mock(mocker)
    _run(PARAMS_IMPORT)

    result = _run(PARAMS_IMPORT)

    assert not result['changed']


def test_trust_ca_import_rolls_out_a_rotated_certificate(mocker):
    testdata = _mock(mocker)
    _run(PARAMS_IMPORT)

    result = _run({**PARAMS_IMPORT, 'certificate': ROTATED_CA_PEM})

    assert result['changed']
    assert len(testdata.mutations()) == 2
    kind, request = testdata.mutations()[1]
    assert kind == 'set'
    assert request['action'] == 'existing'
    assert request['crt_payload'] == ROTATED_CA_PEM


def test_trust_ca_import_ignores_reformatting_of_the_same_certificate(mocker):
    # a certificate that round-tripped through the API comes back re-wrapped;
    # comparing the PEM text would report a change on every single run
    testdata = _mock(mocker)
    _run(PARAMS_IMPORT)

    rewrapped = ROOT_CA_PEM.replace('\n', '\r\n').replace(
        '-----BEGIN CERTIFICATE-----\r\n', '-----BEGIN CERTIFICATE-----\r\n\r\n'
    )
    result = _run({**PARAMS_IMPORT, 'certificate': rewrapped})

    assert not result['changed']
    assert len(testdata.mutations()) == 1


def test_trust_ca_import_carries_the_private_key_when_given(mocker):
    testdata = _mock(mocker)

    result = _run({**PARAMS_IMPORT, 'private_key': ROOT_CA_KEY})

    assert result['changed']
    assert testdata.mutations()[0][1]['prv_payload'] == ROOT_CA_KEY


def test_trust_ca_import_without_a_key_does_not_blank_a_stored_one(mocker):
    # the OpenVPN CA in the fixture was generated by the firewall, so it has a
    # private key. Adopting it by certificate must not throw that key away.
    testdata = _mock(mocker)
    uuid = next(iter(testdata.state))
    stored_key = testdata.state[uuid]['prv_payload']

    _run({**PARAMS_IMPORT, 'description': 'OpenVPN', 'certificate': ROOT_CA_PEM})

    assert testdata.state[uuid]['prv_payload'] == stored_key


def test_trust_ca_import_rejects_something_that_is_not_a_certificate(mocker):
    _mock(mocker)

    with pytest.raises(AnsibleError, match='not a valid PEM certificate'):
        _run({**PARAMS_IMPORT, 'certificate': ROOT_CA_KEY})


def test_trust_ca_import_rejects_an_undecodable_body(mocker):
    _mock(mocker)
    broken = '-----BEGIN CERTIFICATE-----\nnot base64 !!!\n-----END CERTIFICATE-----\n'

    with pytest.raises(AnsibleError, match='not a valid PEM certificate'):
        _run({**PARAMS_IMPORT, 'certificate': broken})


def test_trust_ca_without_a_certificate_still_generates_internally(mocker):
    testdata = _mock(mocker)

    result = _run({**PARAMS, 'certificate': None, 'private_key': None})

    assert result['changed']
    assert testdata.mutations()[0][1]['action'] == 'internal'


def test_trust_ca_import_needs_only_a_description_and_a_certificate(mocker):
    # the shape a trust-store play actually uses: no subject, no key-type, no
    # country - all of that lives in the certificate being imported
    testdata = _mock(mocker)
    minimal = {
        **{k: None for k in PARAMS},
        'description': 'Hartland CA',
        'certificate': ROOT_CA_PEM,
        'private_key': None,
        'match_fields': ['description'],
        'state': 'present',
        'ca': '',
    }

    result = _run(minimal)
    assert result['changed']
    assert testdata.mutations()[0][1]['action'] == 'existing'

    assert not _run(minimal)['changed']
    assert len(testdata.mutations()) == 1


def test_trust_ca_country_is_not_required_when_importing():
    # 'country' is only needed to generate a CA - an imported one carries its own
    # subject. It cannot stay an argspec-level required_if, because that is
    # enforced before the module can tell the two apart.
    # pylint: disable=C0415
    import ast
    import pathlib

    src = pathlib.Path(__file__).parents[2].joinpath('modules', 'trust_ca.py').read_text()
    call = next(
        n for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'AnsibleModule'
    )
    assert 'required_if' not in [kw.arg for kw in call.keywords]


def test_trust_ca_generating_without_a_country_still_fails(mocker):
    _mock(mocker)

    with pytest.raises(AnsibleError, match='country'):
        _run({**PARAMS, 'country': None, 'certificate': None, 'private_key': None})
