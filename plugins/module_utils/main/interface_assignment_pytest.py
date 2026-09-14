from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.interface_assignment import Assignment


def test_assignment_targets_the_model_controller():
    assert Assignment.API_MOD == 'interfaces'
    assert Assignment.API_CONT == 'assignment'
    assert Assignment.API_KEY_PATH == 'interface'


def test_assignment_uses_the_item_api():
    # searchItem/getItem/setItem/addItem/delItem as shipped in OPNsense 26.7
    assert Assignment.CMDS == {
        'add': 'add_item',
        'del': 'del_item',
        'set': 'set_item',
        'search': 'search_item',
        'detail': 'get_item',
    }


def test_assignment_items_are_keyed_by_identifier_not_uuid():
    # the model re-uses the config.xml interface key ('lan', 'optN') as uuid
    assert Assignment.FIELD_ID == 'identifier'
    assert Assignment.field_pk.fget(Assignment) == 'uuid'


def test_assignment_never_compares_the_identifier():
    # OPNsense allocates it at creation time - it identifies, it never changes
    assert 'identifier' not in Assignment.FIELDS_CHANGE
    assert Assignment.FIELDS_CHANGE == ['device', 'description', 'lock']


def test_assignment_translates_to_the_legacy_field_names():
    assert Assignment.FIELDS_TRANSLATE['device'] == 'if'
    assert Assignment.FIELDS_TRANSLATE['description'] == 'descr'


def test_assignment_reads_the_device_as_a_select_field():
    assert 'device' in Assignment.FIELDS_TYPING['select']
    assert 'lock' in Assignment.FIELDS_TYPING['bool']
