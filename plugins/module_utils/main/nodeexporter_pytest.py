from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.nodeexporter import General


def test_nodeexporter_targets_the_general_settings_object():
    assert General.API_MOD == 'nodeexporter'
    assert General.API_CONT == 'general'
    assert General.API_KEY_PATH == 'general'
    assert General.API_KEY_PATH_REQ == General.API_KEY_PATH


def test_nodeexporter_translates_api_field_names():
    assert General.FIELDS_TRANSLATE['listen_address'] == 'listenaddress'
    assert General.FIELDS_TRANSLATE['listen_port'] == 'listenport'


def test_nodeexporter_collectors_are_booleans():
    collectors = [
        'cpu', 'exec', 'filesystem', 'loadavg', 'meminfo', 'netdev', 'time',
        'devstat', 'ntp', 'zfs',
    ]

    for collector in collectors:
        assert collector in General.FIELDS_CHANGE
        assert collector in General.FIELDS_TYPING['bool']


def test_nodeexporter_leaves_the_unused_interrupts_toggle_unmanaged():
    # the plugins config-template ignores it; an absent key is left untouched by setNodes
    assert 'interrupts' not in General.FIELDS_CHANGE
    assert 'interrupts' not in General.FIELDS_ALL


def test_nodeexporter_listen_port_is_a_validated_int():
    assert General.FIELDS_TYPING['int'] == ['listen_port']
    assert General.INT_VALIDATIONS['listen_port'] == {'min': 1, 'max': 65535}
