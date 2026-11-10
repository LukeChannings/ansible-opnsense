from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.translate import \
    get_selected

def find_assignment(existing: list, identifier: str, device: str) -> (dict, None):
    """Picks the existing assignment a declaration is about.

    An identifier names exactly one assignment and OPNsense never reuses it, so
    when one is given it decides the match on its own. Falling back to the
    device here would be actively wrong: a device belongs to whichever
    assignment holds it TODAY, and the one moment someone declares an
    identifier that does not exist yet is the moment they are moving a device
    off another interface -- which would then be adopted and rewritten, lock
    and description and all, instead of a new interface being created.

    Without an identifier the device is all there is to go on, which is how an
    existing table is adopted without naming every identifier by hand.
    """
    if not is_unset(identifier):
        for assignment in existing:
            if assignment['identifier'] == identifier:
                return assignment

        return None

    for assignment in existing:
        if get_selected(assignment.get('device', {})) == device:
            return assignment

    return None


class Assignment(BaseModule):
    FIELD_ID = 'identifier'
    CMDS = {
        'add': 'add_item',
        'del': 'del_item',
        'set': 'set_item',
        'search': 'search_item',
        'detail': 'get_item',
    }
    API_KEY_PATH = 'interface'
    API_MOD = 'interfaces'
    API_CONT = 'assignment'
    # todo: implement the other ~20 fields
    FIELDS_CHANGE = ['description', 'device', 'lock']
    FIELDS_ALL = [FIELD_ID]
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TRANSLATE = {
        'device': 'if',
        'description': 'descr',
        'disable_vlan_hw_filter': 'disablevlanhwfilter',
        'dhcp_reject_from': 'dhcprejectfrom',
        'dhcp_vlan_prio': 'dhcpvlanprio',
        'dhcpv6_vlan_prio': 'dhcp6vlanprio',
        'dhcpv6_ia_pd_len': 'dhcp6-ia-pd-len',
        'track6_interface': 'track6-interface',
        'gateway_v6': 'gatewayv6',
    }
    FIELDS_TYPING = {
        'str': ['description', 'identifier'],
        'bool': ['lock'],
        'select': [
            'device', 'media', 'disable_vlan_hw_filter', 'type4', 'type6', 'dhcp_reject_from', 'dhcp_vlan_prio',
            'dhcpv6_vlan_prio', 'dhcpv6_ia_pd_len', 'track6_interface', 'gateway', 'gateway_v6',
        ],
    }
    EXIST_ATTR = 'assignment'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.assignment = {}

    def _find_device(self) -> None:
        match = find_assignment(
            existing=self.get_existing(),
            identifier=self.p['identifier'],
            device=self.p['device'],
        )

        if match is not None:
            self.exists = True
            self.e = match
            self.p['identifier'] = match['identifier']

    def check(self) -> None:
        self._find_device()

        if self.p['state'] == 'absent':
            if is_unset(self.p['identifier']):
                self.m.fail_json("You need to provide a 'identifier' to delete an interface-assignment!")

            if self.exists and self.e['lock']:
                self.m.fail_json("You need to unlock the interface before you delete an interface-assignment!")

        if self.p['state'] == 'present' and not self.exists:
            if is_unset(self.p['device']):
                self.m.fail_json("You need to provide a 'device' to create an interface-assignment!")

        self._base_check()
