from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.netflow import General


def test_netflow_drives_the_get_set_config_actions():
    # the controller extends ApiControllerBase - there is no 'get'/'set' pair
    assert General.API_MOD == 'diagnostics'
    assert General.API_CONT == 'netflow'
    assert General.CMDS['search'] == 'getconfig'
    assert General.CMDS['set'] == 'setconfig'
    assert General.API_KEY_PATH == 'netflow'
    assert General.API_KEY_PATH_REQ == General.API_KEY_PATH


def test_netflow_manages_every_model_field():
    assert General.FIELDS_CHANGE == [
        'interfaces', 'egress_only', 'version', 'targets', 'capture_local',
        'active_timeout', 'inactive_timeout',
    ]
    assert General.FIELDS_ALL == General.FIELDS_CHANGE


def test_netflow_translates_the_nested_model_paths():
    assert General.FIELDS_TRANSLATE == {
        'interfaces': ('capture', 'interfaces'),
        'egress_only': ('capture', 'egress_only'),
        'version': ('capture', 'version'),
        'targets': ('capture', 'targets'),
        'capture_local': ('collect', 'enable'),
        'active_timeout': 'activeTimeout',
        'inactive_timeout': 'inactiveTimeout',
    }
    assert General.FIELDS_TRANSLATE.keys() <= set(General.FIELDS_ALL)


def test_netflow_enabled_is_derived_rather_than_stored():
    # the model has no enabled-flag; it is expressed through the captured-interface list
    assert 'enabled' not in General.FIELDS_ALL
    assert 'enabled' not in General.FIELDS_TRANSLATE


def test_netflow_interface_and_target_lists_are_multi_selects():
    assert General.FIELDS_TYPING['list'] == ['interfaces', 'egress_only', 'targets']
    assert General.FIELDS_TYPING['select'] == ['version']


def test_netflow_timeouts_are_validated_ints():
    assert General.FIELDS_TYPING['int'] == ['active_timeout', 'inactive_timeout']
    assert General.INT_VALIDATIONS['active_timeout'] == {'min': 1, 'max': 86400}
    assert General.INT_VALIDATIONS['inactive_timeout'] == {'min': 1, 'max': 86400}


def test_netflow_reloads_via_its_own_controller():
    # reconfigure lives on the netflow controller itself, not on a service-controller
    assert not hasattr(General, 'API_CONT_REL')
    assert General.API_CMD_REL == 'reconfigure'


def test_netflow_accepts_ipv4_and_bracketed_ipv6_targets():
    for target in ['127.0.0.1:2056', '192.168.1.50:2055', '[fd00::50]:2055', '[::1]:1']:
        assert General._is_ip_port(target)


def test_netflow_rejects_targets_without_a_usable_port():
    for target in [
        '192.168.1.50', '192.168.1.50:', '192.168.1.50:0', '192.168.1.50:65536',
        '192.168.1.50:http', 'fd00::50:2055', '[fd00::50]', 'collector.example.com:2055',
    ]:
        assert not General._is_ip_port(target)
