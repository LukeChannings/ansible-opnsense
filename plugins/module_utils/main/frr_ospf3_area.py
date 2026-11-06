from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_ip4, is_ip6_network
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class Area(BaseModule):
    FIELD_ID = 'area'
    CMDS = {
        'add': 'addArea',
        'del': 'delArea',
        'set': 'setArea',
        'search': 'get',
        'toggle': 'toggleArea',
    }
    API_KEY_PATH = 'ospf6.areas.area'
    API_MOD = 'quagga'
    API_CONT = 'ospf6settings'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = ['ranges', 'type', 'prefix_list_in', 'prefix_list_out']
    FIELDS_ALL = [FIELD_ID, 'enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TRANSLATE = {
        'area': 'id',
        'prefix_list_in': 'linkedPrefixlistIn',
        'prefix_list_out': 'linkedPrefixlistOut',
    }
    FIELDS_TYPING = {
        'bool': ['enabled'],
        'list': ['ranges'],
        'select': ['type', 'prefix_list_in', 'prefix_list_out'],
    }
    FIELDS_VALUE_MAPPING = {
        # the model's blank option is shown as 'normal' in the web-UI
        'type': {'normal': ''},
    }
    EXIST_ATTR = 'area'
    SEARCH_ADDITIONAL = {
        'existing_prefixes': 'ospf6.prefixlists.prefixlist',
    }

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.area = {}
        self.existing_prefixes = None

    def check(self) -> None:
        if self.p['state'] == 'present':
            if not is_ip4(self.p['area']):
                self.m.fail_json(
                    "The provided area-id is invalid: "
                    f"'{self.p['area']}' - it has to be in dotted format like '0.0.0.0'!"
                )

            for entry in self.p['ranges']:
                if not is_ip6_network(entry):
                    self.m.fail_json(
                        "The provided range is not a valid IPv6 network: "
                        f"'{entry}'!"
                    )

        self._base_check()

        if self.p['state'] == 'present':
            # the prefix-list links are relations to 'ospf6.prefixlists.prefixlist' -
            # the API wants the uuid of a prefix-list entry
            self.find_single_link(
                field='prefix_list_in',
                existing=self.existing_prefixes,
            )
            self.find_single_link(
                field='prefix_list_out',
                existing=self.existing_prefixes,
            )

    def get_existing(self) -> list:
        existing = []

        for entry in self._base_get_existing():
            # resolve the prefix-list uuids back to their names so they stay comparable
            for field in ['prefix_list_in', 'prefix_list_out']:
                if entry[field] not in [None, ''] and entry[field] in self.existing_prefixes:
                    entry[field] = self.existing_prefixes[entry[field]]['name']

            existing.append(entry)

        return existing
