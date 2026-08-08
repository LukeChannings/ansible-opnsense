from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_ip4, is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class Relay(BaseModule):
    FIELD_ID = 'instance_id'
    CMDS = {
        'add': 'add_relay',
        'del': 'del_relay',
        'set': 'set_relay',
        'search': 'get',
        'toggle': 'toggle_relay',
    }
    API_KEY_PATH = 'udpbroadcastrelay.udpbroadcastrelay'
    API_KEY_PATH_REQ = 'udpbroadcastrelay'
    API_MOD = 'udpbroadcastrelay'
    API_CONT = 'settings'
    API_CONT_REL = 'service'
    API_CMD_REL = 'reload'
    FIELDS_CHANGE = [
        'interfaces', 'multicast_address', 'source_address', 'listen_port',
        'revert_ttl', 'description',
    ]
    FIELDS_ALL = [FIELD_ID, 'enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TRANSLATE = {
        'instance_id': 'InstanceID',
        'multicast_address': 'multicastaddress',
        'source_address': 'sourceaddress',
        'listen_port': 'listenport',
        'revert_ttl': 'RevertTTL',
    }
    FIELDS_TYPING = {
        'bool': ['enabled', 'revert_ttl'],
        'list': ['interfaces', 'multicast_address'],
        'int': ['instance_id', 'listen_port'],
    }
    INT_VALIDATIONS = {
        'instance_id': {'min': 1, 'max': 63},
        'listen_port': {'min': 1, 'max': 65535},
    }
    EXIST_ATTR = 'relay'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.relay = {}

    def check(self) -> None:
        if self.p['state'] == 'present':
            for field in ['instance_id', 'listen_port']:
                if is_unset(self.p[field]):
                    self.m.fail_json(f"You need to provide a '{field}' to create a relay!")

            if len(self.p['interfaces']) < 2:
                self.m.fail_json(
                    "You need to provide at least two 'interfaces' to relay between!"
                )

            for address in self.p['multicast_address'] + [self.p['source_address']]:
                if not is_unset(address) and not is_ip4(address):
                    self.m.fail_json(
                        f"Value '{address}' is not a valid IPv4-Address! "
                        "The udpbroadcastrelay service does not support IPv6."
                    )

        self._base_check()
