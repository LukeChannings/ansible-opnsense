from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.interface_assignment import \
    find_assignment


def _assignment(identifier: str, device: str) -> dict:
    return {
        'identifier': identifier,
        'device': {device: {'value': device, 'selected': 1}},
        'description': identifier.upper(),
        'lock': True,
    }


EXISTING = [
    _assignment('lan', 'ix0'),
    _assignment('opt4', 'vlan0.40'),
]


def test_an_identifier_that_exists_is_the_match():
    assert find_assignment(EXISTING, identifier='opt4', device='bridge0')['identifier'] == 'opt4'


def test_a_new_identifier_does_not_adopt_whoever_holds_the_device():
    # the case this exists for: opt4 is being moved from vlan0.40 to a bridge
    # and opt11 declared for the vlan it leaves behind. Matching on the device
    # would hand back opt4 -- renaming and unlocking the interface the whole
    # fleet routes through -- instead of creating opt11
    assert find_assignment(EXISTING, identifier='opt11', device='vlan0.40') is None


def test_without_an_identifier_the_device_adopts_the_existing_entry():
    # how a live table is adopted without naming every identifier by hand
    assert find_assignment(EXISTING, identifier=None, device='vlan0.40')['identifier'] == 'opt4'


def test_an_unknown_device_and_no_identifier_matches_nothing():
    assert find_assignment(EXISTING, identifier='', device='vlan0.99') is None
