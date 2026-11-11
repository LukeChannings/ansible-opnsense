from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_ip4, is_ip6
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import GeneralModule


class General(GeneralModule):
    CMDS = {
        'set': 'setconfig',
        'search': 'getconfig',
    }
    API_KEY_PATH = 'netflow'
    API_KEY_PATH_REQ = API_KEY_PATH
    API_MOD = 'diagnostics'
    API_CONT = 'netflow'
    API_CMD_REL = 'reconfigure'
    FIELDS_CHANGE = [
        'interfaces', 'egress_only', 'version', 'targets', 'capture_local',
        'active_timeout', 'inactive_timeout',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    FIELDS_TRANSLATE = {
        'interfaces': ('capture', 'interfaces'),
        'egress_only': ('capture', 'egress_only'),
        'version': ('capture', 'version'),
        'targets': ('capture', 'targets'),
        'capture_local': ('collect', 'enable'),
        'active_timeout': 'activeTimeout',
        'inactive_timeout': 'inactiveTimeout',
    }
    FIELDS_TYPING = {
        'bool': ['capture_local'],
        'int': ['active_timeout', 'inactive_timeout'],
        'list': ['interfaces', 'egress_only', 'targets'],
        'select': ['version'],
    }
    INT_VALIDATIONS = {
        'active_timeout': {'min': 1, 'max': 86400},
        'inactive_timeout': {'min': 1, 'max': 86400},
    }
    LOCAL_TARGET = '127.0.0.1:2056'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)

    def check(self) -> None:
        for target in self.p['targets']:
            if not self._is_ip_port(target):
                self.m.fail_json(
                    f"Value '{target}' is not a valid NetFlow target! "
                    "Expected '<ipv4>:<port>' or '[<ipv6>]:<port>'."
                )

        for interface in self.p['egress_only']:
            if interface not in self.p['interfaces']:
                self.m.fail_json(
                    f"Interface '{interface}' is listed as 'egress_only' but is not "
                    "captured - add it to 'interfaces' or drop it."
                )

        if self.p['capture_local'] and self.LOCAL_TARGET not in self.p['targets']:
            self.p['targets'].append(self.LOCAL_TARGET)

        if self.p['enabled']:
            for field in ['interfaces', 'targets']:
                if len(self.p[field]) == 0:
                    self.m.fail_json(
                        f"You need to provide at least one '{field}' entry to capture "
                        "NetFlow data - or set 'enabled' to false to stop the capture."
                    )

        else:
            self.p['interfaces'] = []
            self.p['egress_only'] = []

        self._base_check()

    def search_call(self) -> dict:
        simplified = self.simplify_existing(self.search())

        for opn_field in self.FIELDS_TRANSLATE.values():
            if isinstance(opn_field, tuple):
                simplified.pop(opn_field[0], None)

        simplified['enabled'] = len(simplified['interfaces']) > 0 and len(simplified['targets']) > 0
        return simplified

    @staticmethod
    def _is_ip_port(target: str) -> bool:
        if target.startswith('['):
            address, sep, port = target.partition(']:')
            valid_address = sep != '' and is_ip6(address[1:])

        else:
            address, sep, port = target.rpartition(':')
            valid_address = sep != '' and is_ip4(address)

        if not valid_address or not port.isdigit():
            return False

        return 1 <= int(port) <= 65535
