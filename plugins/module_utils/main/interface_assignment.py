from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.main import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


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
    FIELDS_CHANGE = ['device', 'description', 'lock']
    FIELDS_ALL = [FIELD_ID]
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TRANSLATE = {
        'device': 'if',
        'description': 'descr',
    }
    FIELDS_TYPING = {
        'select': ['device'],
        'bool': ['lock'],
    }
    EXIST_ATTR = 'assignment'
    TIMEOUT = 60.0  # reconfigure may re-run dhcp/dhcp6 on the interface

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.assignment = {}

    def check(self) -> None:
        for field in self.p['match_fields']:
            if is_unset(self.p[field]):
                self.m.fail_json(
                    f"You need to provide a '{field}' to match the assignment on!"
                )

        if self.p['state'] == 'present' and is_unset(self.p['device']):
            self.m.fail_json(
                "You need to provide a 'device' to assign an interface!"
            )

        self._base_check()

        if self.p['state'] == 'present' and not self.exists and \
                'identifier' in self.p['match_fields']:
            # the API allocates the next free 'optN' itself; a chosen
            # identifier can only ever match an existing assignment
            self.m.fail_json(
                "A new assignment cannot be matched on its 'identifier' as OPNsense "
                "allocates it at creation time. Use match_fields=['description'] to "
                'create assignments.'
            )

    def update(self) -> None:
        self._base_update(enable_switch=False)
