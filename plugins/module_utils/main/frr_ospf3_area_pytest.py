import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf3_area import \
    Area
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
    MockAnsibleModule, AnsibleError
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.frr_area_testdata import \
    AREA_UUID_BACKBONE, PREFIX_NAME_IN, PREFIX_NAME_OUT, PREFIX_UUID_IN, PREFIX_UUID_OUT, \
    PREFIXLISTS

BASE_PARAMS = dict(
    area='0.0.0.0',
    enabled=True,
    ranges=['2001:db8:1::/48', '2001:db8:2::/48'],
    type='normal',
    prefix_list_in=PREFIX_NAME_IN,
    prefix_list_out=None,
    state='present',
    reload=False,
)


def _module(**overrides) -> MockAnsibleModule:
    module = MockAnsibleModule()
    module.params.update({**BASE_PARAMS, **overrides})
    return module


def _area(module: MockAnsibleModule) -> Area:
    return Area(module=module, result={'changed': False, 'diff': {'before': {}, 'after': {}}})


# --- wiring --------------------------------------------------------------------

def test_targets_the_area_collection_of_the_ospf6_model():
    assert Area.API_KEY_PATH == 'ospf6.areas.area'
    assert Area.API_CONT == 'ospf6settings'
    assert Area.API_MOD == 'quagga'
    assert Area.API_CONT_REL == 'service'


def test_uses_the_area_endpoints():
    assert Area.CMDS['add'] == 'addArea'
    assert Area.CMDS['set'] == 'setArea'
    assert Area.CMDS['del'] == 'delArea'
    assert Area.CMDS['toggle'] == 'toggleArea'


def test_the_area_id_is_the_match_key():
    # 'id' carries a UniqueConstraint server-side, so it identifies the entry
    assert Area.FIELD_ID == 'area'
    assert Area.FIELDS_TRANSLATE['area'] == 'id'


def test_prefix_lists_are_pulled_from_the_same_get_response():
    assert Area.SEARCH_ADDITIONAL['existing_prefixes'] == 'ospf6.prefixlists.prefixlist'


# --- validation ----------------------------------------------------------------

def test_a_non_dotted_area_id_is_rejected():
    inst = _area(_module(area='0'))

    with pytest.raises(AnsibleError) as err:
        inst.check()

    assert '0' in str(err.value)


def test_an_ipv4_range_is_rejected_on_an_ospfv3_area():
    inst = _area(_module(ranges=['10.0.1.0/24']))

    with pytest.raises(AnsibleError) as err:
        inst.check()

    assert '10.0.1.0/24' in str(err.value)


def test_an_invalid_area_id_is_not_validated_when_removing(mocker):
    inst = _area(_module(area='0', state='absent'))
    inst.existing_prefixes = PREFIXLISTS
    mocker.patch.object(inst, '_base_check')

    # must get far enough to attempt the removal rather than fail on validation
    inst.check()


# --- relation resolution -------------------------------------------------------

def test_check_resolves_prefix_list_names_to_their_uuids_for_the_api(mocker):
    inst = _area(_module(prefix_list_in=PREFIX_NAME_IN, prefix_list_out=PREFIX_NAME_OUT))
    inst.existing_prefixes = PREFIXLISTS
    mocker.patch.object(inst, '_base_check')

    inst.check()

    assert inst.p['prefix_list_in'] == PREFIX_UUID_IN
    assert inst.p['prefix_list_out'] == PREFIX_UUID_OUT


def test_check_fails_with_the_prefix_list_name_that_was_not_found(mocker):
    inst = _area(_module(prefix_list_in='DOES_NOT_EXIST'))
    inst.existing_prefixes = PREFIXLISTS
    mocker.patch.object(inst, '_base_check')

    with pytest.raises(AnsibleError) as err:
        inst.check()

    assert 'DOES_NOT_EXIST' in str(err.value)


def test_get_existing_maps_the_prefix_list_uuids_back_to_their_names(mocker):
    inst = _area(_module())
    inst.existing_prefixes = PREFIXLISTS
    mocker.patch.object(
        inst, '_base_get_existing',
        return_value=[{
            'area': '0.0.0.0',
            'prefix_list_in': PREFIX_UUID_IN,
            'prefix_list_out': PREFIX_UUID_OUT,
        }],
    )

    assert inst.get_existing() == [{
        'area': '0.0.0.0',
        'prefix_list_in': PREFIX_NAME_IN,
        'prefix_list_out': PREFIX_NAME_OUT,
    }]


def test_get_existing_leaves_an_unlinked_prefix_list_untouched(mocker):
    inst = _area(_module())
    inst.existing_prefixes = PREFIXLISTS
    mocker.patch.object(
        inst, '_base_get_existing',
        return_value=[{'area': '0.0.0.0', 'prefix_list_in': '', 'prefix_list_out': ''}],
    )

    assert inst.get_existing() == [
        {'area': '0.0.0.0', 'prefix_list_in': '', 'prefix_list_out': ''}
    ]


# --- end-to-end against a canned os-frr 2.0_4 'get' ----------------------------

def _run(mocker, params: dict):
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
        pytest_mock_http_responses
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.frr_area_testdata import \
        Testdata_frr_ospf6_2_0_4
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper

    testdata = Testdata_frr_ospf6_2_0_4()
    pytest_mock_http_responses(mocker=mocker, handler=testdata)

    module = MockAnsibleModule()
    module.params.update(params)
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    module_wrapper(Area(module=module, result=result))
    return result, testdata


def test_run_against_a_matching_area_is_idempotent(mocker):
    # 'type' normal round-trips through the blank option, 'ranges' through an
    # AsList option-dict and 'prefix_list_in' through a relation-dict - any of
    # those failing to reduce would report a phantom change
    result, testdata = _run(mocker, BASE_PARAMS)

    assert not result['changed']
    assert testdata.writes == []


def test_a_changed_area_writes_the_prefix_list_uuid_not_its_name(mocker):
    result, testdata = _run(mocker, {**BASE_PARAMS, 'prefix_list_out': PREFIX_NAME_OUT})

    assert result['changed']
    assert len(testdata.written_areas()) == 1
    assert testdata.written_areas()[0]['linkedPrefixlistOut'] == PREFIX_UUID_OUT


def test_the_order_of_ranges_does_not_signal_a_change(mocker):
    # the API returns 'ranges' sorted - a differently ordered play must stay idempotent
    result, testdata = _run(
        mocker, {**BASE_PARAMS, 'ranges': ['2001:db8:2::/48', '2001:db8:1::/48']}
    )

    assert not result['changed']
    assert testdata.writes == []


def test_a_changed_area_writes_ranges_as_a_comma_separated_list(mocker):
    result, testdata = _run(
        mocker, {**BASE_PARAMS, 'ranges': ['2001:db8:3::/48', '2001:db8:1::/48', '2001:db8:2::/48']}
    )

    assert result['changed']
    assert testdata.written_areas()[0]['ranges'] == \
        '2001:db8:1::/48,2001:db8:2::/48,2001:db8:3::/48'


def test_a_normal_area_is_written_as_the_blank_type(mocker):
    _, testdata = _run(mocker, {**BASE_PARAMS, 'ranges': []})

    assert testdata.written_areas()[0]['type'] == ''


def test_an_nssa_area_is_written_verbatim(mocker):
    _, testdata = _run(mocker, {**BASE_PARAMS, 'type': 'nssa no-summary'})

    assert testdata.written_areas()[0]['type'] == 'nssa no-summary'


def test_a_new_area_is_added_rather_than_set(mocker):
    result, testdata = _run(mocker, {**BASE_PARAMS, 'area': '0.0.0.9', 'ranges': []})

    assert result['changed']
    assert [kind for kind, _, _ in testdata.writes] == ['add']
    assert testdata.written_areas()[0]['id'] == '0.0.0.9'


def test_removing_an_area_deletes_it(mocker):
    result, testdata = _run(mocker, {**BASE_PARAMS, 'state': 'absent'})

    assert result['changed']
    assert AREA_UUID_BACKBONE not in testdata.state
