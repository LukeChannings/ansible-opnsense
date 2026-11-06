from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class Interface(BaseModule):
    CMDS = {
        'add': 'addInterface',
        'del': 'delInterface',
        'set': 'setInterface',
        'search': 'get',
        'toggle': 'toggleInterface',
    }
    API_KEY_PATH = 'ospf6.interfaces.interface'
    API_MOD = 'quagga'
    API_CONT = 'ospf6settings'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'interface', 'area', 'passive', 'cost', 'cost_demoted', 'carp_depend_on',
        'hello_interval', 'dead_interval', 'retransmit_interval', 'transmit_delay',
        'priority', 'network_type',
    ]
    FIELDS_ALL = ['enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    INT_VALIDATIONS = {
        'cost': {'min': 0, 'max': 4294967295},
        'hello_interval': {'min': 0, 'max': 4294967295},
        'dead_interval': {'min': 0, 'max': 4294967295},
        'retransmit_interval': {'min': 0, 'max': 4294967295},
        'transmit_delay': {'min': 0, 'max': 4294967295},
        'priority': {'min': 0, 'max': 4294967295},
        'cost_demoted': {'min': 1, 'max': 65535},
    }
    FIELDS_TRANSLATE = {
        'interface': 'interfacename',
        'hello_interval': 'hellointerval',
        'dead_interval': 'deadinterval',
        'retransmit_interval': 'retransmitinterval',
        'transmit_delay': 'transmitdelay',
        'network_type': 'networktype',
    }
    FIELDS_TYPING = {
        'bool': ['enabled', 'passive'],
        'select': ['interface', 'carp_depend_on', 'network_type', 'area'],
    }
    EXIST_ATTR = 'int'
    SEARCH_ADDITIONAL = {
        'existing_areas': 'ospf6.areas.area',
    }

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.int = {}
        self.existing_areas = None

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['area']):
                self.m.fail_json(
                    'To create a OSPFv3 interface you need to provide its area!'
                )

        self._base_check()

        if self.p['state'] == 'present':
            # 'area' is a relation to an entry of 'ospf6.areas.area' - the API wants its uuid
            self.find_single_link(
                field='area',
                existing=self.existing_areas,
                existing_field_id='id',
            )

    def get_existing(self) -> list:
        existing = []

        for entry in self._base_get_existing():
            # resolve the area-uuid back to its id ('0.0.0.0') so it stays comparable
            if entry['area'] not in [None, ''] and entry['area'] in self.existing_areas:
                entry['area'] = self.existing_areas[entry['area']]['id']

            existing.append(entry)

        return existing
