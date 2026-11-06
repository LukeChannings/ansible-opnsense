from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.tailscale_general import General


def test_tailscale_general_targets_the_settings_object():
    assert General.API_MOD == 'tailscale'
    assert General.API_CONT == 'settings'
    assert General.API_KEY_PATH == 'settings'
    assert General.API_KEY_PATH_REQ == General.API_KEY_PATH


def test_tailscale_general_manages_every_scalar_model_field():
    assert General.FIELDS_CHANGE == [
        'enabled', 'login_timeout', 'listen_port', 'accept_dns',
        'advertise_exit_node', 'use_exit_node', 'accept_subnet_routes',
        'enable_ssh', 'disable_snat',
    ]
    assert General.FIELDS_ALL == General.FIELDS_CHANGE


def test_tailscale_general_leaves_the_advertised_subnets_to_the_subnet_module():
    # 'subnets.subnet4' is an ArrayField in the same settings-object; keeping it out
    # of FIELDS_ALL keeps it out of the set-payload
    assert 'subnets' not in General.FIELDS_ALL


def test_tailscale_general_translates_the_camel_case_api_fields():
    assert General.FIELDS_TRANSLATE == {
        'login_timeout': 'loginTimeout',
        'listen_port': 'listenPort',
        'accept_dns': 'acceptDNS',
        'advertise_exit_node': 'advertiseExitNode',
        'use_exit_node': 'useExitNode',
        'accept_subnet_routes': 'acceptSubnetRoutes',
        'enable_ssh': 'enableSSH',
        'disable_snat': 'disableSNAT',
    }
    assert General.FIELDS_TRANSLATE.keys() <= set(General.FIELDS_ALL)


def test_tailscale_general_toggles_are_booleans():
    for field in [
        'enabled', 'accept_dns', 'advertise_exit_node', 'accept_subnet_routes',
        'enable_ssh', 'disable_snat',
    ]:
        assert field in General.FIELDS_TYPING['bool']


def test_tailscale_general_numeric_fields_are_validated_ints():
    assert General.FIELDS_TYPING['int'] == ['login_timeout', 'listen_port']
    assert General.INT_VALIDATIONS['listen_port'] == {'min': 1, 'max': 65535}
    assert General.INT_VALIDATIONS['login_timeout']['min'] == 1


def test_tailscale_general_exit_node_is_a_select():
    # ExitNodeField is a BaseListField - the API returns an option-list, not a string
    assert General.FIELDS_TYPING['select'] == ['use_exit_node']


def test_tailscale_general_reloads_via_the_service_controller():
    assert General.API_CONT_REL == 'service'
    assert General.API_CMD_REL == 'reconfigure'
