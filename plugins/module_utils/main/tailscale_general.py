from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.main import is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.translate import \
    get_key_by_value_from_selection
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import GeneralModule


class General(GeneralModule):
    CMDS = {
        'set': 'set',
        'search': 'get',
    }
    API_KEY_PATH = 'settings'
    API_KEY_PATH_REQ = API_KEY_PATH
    API_MOD = 'tailscale'
    API_CONT = 'settings'
    API_CONT_REL = 'service'
    API_CMD_REL = 'reconfigure'
    FIELDS_CHANGE = [
        'enabled', 'login_timeout', 'listen_port', 'accept_dns',
        'advertise_exit_node', 'use_exit_node', 'accept_subnet_routes',
        'enable_ssh', 'disable_snat',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    FIELDS_TRANSLATE = {
        'login_timeout': 'loginTimeout',
        'listen_port': 'listenPort',
        'accept_dns': 'acceptDNS',
        'advertise_exit_node': 'advertiseExitNode',
        'use_exit_node': 'useExitNode',
        'accept_subnet_routes': 'acceptSubnetRoutes',
        'enable_ssh': 'enableSSH',
        'disable_snat': 'disableSNAT',
    }
    FIELDS_TYPING = {
        'bool': [
            'enabled', 'accept_dns', 'advertise_exit_node',
            'accept_subnet_routes', 'enable_ssh', 'disable_snat',
        ],
        'int': ['login_timeout', 'listen_port'],
        'select': ['use_exit_node'],
    }
    INT_VALIDATIONS = {
        'login_timeout': {'min': 1, 'max': 3600},
        'listen_port': {'min': 1, 'max': 65535},
    }
    FIELD_EXIT_NODE = 'use_exit_node'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)
        self.exit_nodes = {}

    def check(self) -> None:
        self._check_validators()
        self.settings = self.search_call()
        self._resolve_exit_node()
        self._build_diff()

    def search_call(self) -> dict:
        existing = self.search()
        self.exit_nodes = existing.get('useExitNode', {})
        simplified = self.simplify_existing(existing)
        simplified.pop('subnets', None)
        return simplified

    def _resolve_exit_node(self) -> None:
        wanted = self.p[self.FIELD_EXIT_NODE]

        if is_unset(wanted) or wanted in self.exit_nodes:
            return

        by_hostname = get_key_by_value_from_selection(selection=self.exit_nodes, value=wanted)

        if by_hostname is None:
            self.m.fail_json(
                f"Value '{wanted}' is not an exit-node offered by the tailnet! "
                f'Available: {self._available_exit_nodes()}'
            )

        self.p[self.FIELD_EXIT_NODE] = by_hostname

    def _available_exit_nodes(self) -> list:
        return [
            f"{node['value']} ({ip})"
            for ip, node in self.exit_nodes.items()
            if not is_unset(ip)
        ]
