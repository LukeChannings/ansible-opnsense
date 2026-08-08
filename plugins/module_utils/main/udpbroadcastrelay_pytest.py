from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.udpbroadcastrelay import Relay


def test_udpbroadcastrelay_matches_on_instance_id():
    assert Relay.FIELD_ID == 'instance_id'
    assert Relay.FIELD_ID not in Relay.FIELDS_CHANGE
    assert Relay.FIELD_ID in Relay.FIELDS_ALL


def test_udpbroadcastrelay_translates_api_field_names():
    assert Relay.FIELDS_TRANSLATE['instance_id'] == 'InstanceID'
    assert Relay.FIELDS_TRANSLATE['revert_ttl'] == 'RevertTTL'
    assert Relay.FIELDS_TRANSLATE['listen_port'] == 'listenport'


def test_udpbroadcastrelay_multi_value_fields_are_lists():
    assert 'interfaces' in Relay.FIELDS_TYPING['list']
    assert 'multicast_address' in Relay.FIELDS_TYPING['list']
