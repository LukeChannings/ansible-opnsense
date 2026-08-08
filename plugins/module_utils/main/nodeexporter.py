from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_ip
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import GeneralModule


class General(GeneralModule):
    CMDS = {
        'set': 'set',
        'search': 'get',
    }
    API_KEY_PATH = 'general'
    API_KEY_PATH_REQ = API_KEY_PATH
    API_MOD = 'nodeexporter'
    API_CONT = 'general'
    API_CONT_REL = 'service'
    API_CMD_REL = 'reconfigure'
    FIELDS_CHANGE = [
        'enabled', 'listen_address', 'listen_port', 'cpu', 'exec', 'filesystem',
        'loadavg', 'meminfo', 'netdev', 'time', 'devstat', 'ntp', 'zfs',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    FIELDS_TRANSLATE = {
        'listen_address': 'listenaddress',
        'listen_port': 'listenport',
    }
    FIELDS_TYPING = {
        'bool': [
            'enabled', 'cpu', 'exec', 'filesystem', 'loadavg', 'meminfo',
            'netdev', 'time', 'devstat', 'ntp', 'zfs',
        ],
        'int': ['listen_port'],
    }
    INT_VALIDATIONS = {
        'listen_port': {'min': 1, 'max': 65535},
    }

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)

    def check(self) -> None:
        if not is_ip(self.p['listen_address']):
            self.m.fail_json(
                f"Value '{self.p['listen_address']}' is not a valid IP-Address "
                "to listen on!"
            )

        self._base_check()
