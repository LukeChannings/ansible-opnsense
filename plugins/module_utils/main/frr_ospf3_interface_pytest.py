import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf3_interface import \
    Interface
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
    MockAnsibleModule, AnsibleError

# os-frr 2.0 (plugin-commit 737b4834, OSPF6 model 1.1.4+) turned 'area' from a
# TextField into a ModelRelationField pointing at the new 'ospf6.areas.area'
# collection. The API wants the uuid of an area-entry - sending the area-id
# ('0.0.0.0') fails with "Related Area not found.".

AREA_UUID = '2f1a7d4e-9c3b-4a21-8f55-1be0c7d49a10'
EXISTING_AREAS = {
    AREA_UUID: {'enabled': '1', 'id': '0.0.0.0'},
    '7c9e2b10-4d8a-4f33-9b02-66a1d3f5e884': {'enabled': '1', 'id': '0.0.0.1'},
}


def _module(**overrides) -> MockAnsibleModule:
    module = MockAnsibleModule()
    module.params.update({
        'state': 'present',
        'enabled': True,
        'interface': 'opt4',
        'area': '0.0.0.0',
        'passive': False,
        'network_type': 'broadcast',
        'match_fields': ['interface'],
        **overrides,
    })
    return module


def _interface(module: MockAnsibleModule) -> Interface:
    return Interface(module=module, result={'changed': False, 'diff': {'before': {}, 'after': {}}})


def test_area_is_pulled_from_the_same_get_response():
    assert Interface.SEARCH_ADDITIONAL['existing_areas'] == 'ospf6.areas.area'


def test_area_is_typed_as_a_selection():
    # without this the relation-dict from the API never reduces to the area-uuid
    assert 'area' in Interface.FIELDS_TYPING['select']


def test_check_resolves_the_area_id_to_its_uuid_for_the_api(mocker):
    inst = _interface(_module())
    inst.existing_areas = EXISTING_AREAS
    mocker.patch.object(inst, '_base_check')

    inst.check()

    assert inst.p['area'] == AREA_UUID


def test_check_fails_with_the_area_id_when_no_such_area_exists(mocker):
    inst = _interface(_module(area='0.0.0.9'))
    inst.existing_areas = EXISTING_AREAS
    mocker.patch.object(inst, '_base_check')

    with pytest.raises(AnsibleError) as err:
        inst.check()

    assert '0.0.0.9' in str(err.value)


def test_check_does_not_resolve_an_area_when_removing_an_interface(mocker):
    module = _module(state='absent')
    inst = _interface(module)
    inst.existing_areas = EXISTING_AREAS
    mocker.patch.object(inst, '_base_check')

    inst.check()

    assert inst.p['area'] == '0.0.0.0'


def test_get_existing_maps_the_area_uuid_back_to_its_id(mocker):
    inst = _interface(_module())
    inst.existing_areas = EXISTING_AREAS
    mocker.patch.object(
        inst, '_base_get_existing',
        return_value=[{'interface': 'opt4', 'area': AREA_UUID, 'passive': False}],
    )

    assert inst.get_existing() == [{'interface': 'opt4', 'area': '0.0.0.0', 'passive': False}]


def test_get_existing_leaves_an_unresolvable_area_untouched(mocker):
    inst = _interface(_module())
    inst.existing_areas = EXISTING_AREAS
    mocker.patch.object(
        inst, '_base_get_existing',
        return_value=[{'interface': 'opt4', 'area': '', 'passive': False}],
    )

    assert inst.get_existing() == [{'interface': 'opt4', 'area': '', 'passive': False}]


# --- end-to-end against a response captured from a live os-frr 2.0_4 box ------

LIVE_CAPTURE_PARAMS = dict(
    interface='opt4',
    area='0.0.0.0',
    passive=False,
    network_type='broadcast',
    match_fields=['interface'],
    state='present',
    enabled=True,
    reload=False,
    cost=None,
    cost_demoted=65535,
    carp_depend_on=None,
    hello_interval=None,
    dead_interval=None,
    retransmit_interval=None,
    transmit_delay=None,
    priority=None,
)


def _run_against_live_capture(mocker, params: dict):
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
        pytest_mock_http_responses
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.frr_ospf3_interface_testdata import \
        Testdata_frr_2_0_4
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper

    testdata = Testdata_frr_2_0_4()
    pytest_mock_http_responses(mocker=mocker, handler=testdata)

    module = MockAnsibleModule()
    module.params.update(params)
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    module_wrapper(Interface(module=module, result=result))
    return result, testdata


def test_live_capture_run_is_idempotent(mocker):
    # the running config already matches - this must not issue a write at all.
    # before the fix the relation-dict never equalled '0.0.0.0', so every run
    # reported a change and every write was rejected with 'Related Area not found.'
    result, testdata = _run_against_live_capture(mocker, LIVE_CAPTURE_PARAMS)

    assert not result['changed']
    assert testdata.writes == []


def test_live_capture_write_carries_the_area_uuid(mocker):
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.frr_ospf3_interface_testdata import \
        AREA_UUID

    result, testdata = _run_against_live_capture(mocker, {**LIVE_CAPTURE_PARAMS, 'passive': True})

    assert result['changed']
    assert testdata.written_areas() == [AREA_UUID]
    assert '0.0.0.0' not in testdata.written_areas()
