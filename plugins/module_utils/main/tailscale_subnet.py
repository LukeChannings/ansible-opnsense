from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_network, is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class Subnet(BaseModule):
    FIELD_ID = 'subnet'
    CMDS = {
        'add': 'add_subnet',
        'del': 'del_subnet',
        'set': 'set_subnet',
        'search': 'search_subnet',
        'detail': 'get_subnet',
    }
    API_KEY_PATH = 'subnet4'
    API_KEY_PATH_REQ = API_KEY_PATH
    API_MOD = 'tailscale'
    API_CONT = 'settings'
    API_CONT_REL = 'service'
    API_CMD_REL = 'reconfigure'
    FIELDS_CHANGE = ['description']
    FIELDS_ALL = [FIELD_ID]
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TYPING = {}
    EXIST_ATTR = 'route'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.route = {}

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['subnet']):
                self.m.fail_json("You need to provide a 'subnet' to advertise!")

            if '/' not in self.p['subnet'] or not is_network(self.p['subnet'], strict=True):
                self.m.fail_json(
                    f"Value '{self.p['subnet']}' is not a valid network in CIDR-notation! "
                    'Tailscale advertises routes, not hosts - the netmask is mandatory '
                    'and the host-bits have to be unset.'
                )

        self._base_check()
