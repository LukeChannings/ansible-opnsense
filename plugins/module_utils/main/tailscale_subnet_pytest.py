from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.tailscale_subnet import Subnet


def test_tailscale_subnet_matches_on_the_network():
    assert Subnet.FIELD_ID == 'subnet'
    assert Subnet.FIELD_ID not in Subnet.FIELDS_CHANGE
    assert Subnet.FIELD_ID in Subnet.FIELDS_ALL


def test_tailscale_subnet_uses_the_array_field_endpoints_of_the_settings_controller():
    assert Subnet.API_MOD == 'tailscale'
    assert Subnet.API_CONT == 'settings'
    assert Subnet.CMDS == {
        'add': 'add_subnet',
        'del': 'del_subnet',
        'set': 'set_subnet',
        'search': 'search_subnet',
        'detail': 'get_subnet',
    }


def test_tailscale_subnet_unwraps_the_subnet4_key():
    assert Subnet.API_KEY_PATH == 'subnet4'
    assert Subnet.API_KEY_PATH_REQ == Subnet.API_KEY_PATH


def test_tailscale_subnet_carries_no_typed_fields():
    # 'subnet' and 'description' are both plain strings on the API
    assert Subnet.FIELDS_TYPING == {}
    assert Subnet.FIELDS_ALL == ['subnet', 'description']


def test_tailscale_subnet_reloads_via_the_service_controller():
    assert Subnet.API_CONT_REL == 'service'
    assert Subnet.API_CMD_REL == 'reconfigure'
