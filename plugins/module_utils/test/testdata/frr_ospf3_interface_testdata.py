from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.base_testdata import \
    MockOPNsenseController

# Shaped after an 'ospf6settings/get' from a live OPNsense running os-frr 2.0_4
# (plugin-commit c4aee28a1, OSPF6 model 1.1.5), after migration M1_1_4 turned the
# legacy area-id into an explicit area-record. Uuids, router-id and
# interface-descriptions are placeholders - the test asserts on the structure.
#
# Note the shape of 'interfaces.interface.*.area': it is a relation-dict keyed
# by the area-uuid, not the area-id - which is why the module has to resolve it.

AREA_UUID = '0c7035ad-615c-4a67-a7b1-b72a525770b6'
INTERFACE_UUID = 'da098821-706c-4306-8f6c-6d45334d21c4'

AREAS = {
    AREA_UUID: {
        'enabled': '1',
        'id': '0.0.0.0',
        'ranges': {'': {'value': '', 'selected': 1}},
        'linkedPrefixlistIn': {'': {'value': 'None', 'selected': 1}},
        'linkedPrefixlistOut': {'': {'value': 'None', 'selected': 1}},
        'type': {
            '': {'value': 'normal', 'selected': 1},
            'nssa': {'value': 'nssa', 'selected': 0},
            'nssa no-summary': {'value': 'nssa no-summary', 'selected': 0},
        },
    },
}

INTERFACE = {
    'enabled': '1',
    'interfacename': {
        'lan': {'value': 'LAN', 'selected': 0},
        'wan': {'value': 'WAN', 'selected': 0},
        'lo0': {'value': 'Loopback', 'selected': 0},
        'opt1': {'value': 'OPT1', 'selected': 0},
        'opt2': {'value': 'OPT2', 'selected': 0},
        'opt3': {'value': 'OPT3', 'selected': 0},
        'opt4': {'value': 'OPT4', 'selected': 1},
    },
    'area': {AREA_UUID: {'value': '0.0.0.0', 'selected': 1}},
    'passive': '0',
    'cost': '',
    'cost_demoted': '65535',
    'carp_depend_on': {'': {'value': 'None', 'selected': 1}},
    'hellointerval': '',
    'deadinterval': '',
    'retransmitinterval': '',
    'transmitdelay': '',
    'priority': '',
    'bfd': '0',
    'networktype': {
        '': {'value': 'None', 'selected': 0},
        'broadcast': {'value': 'Broadcast multi-access network', 'selected': 1},
        'point-to-point': {'value': 'Point-to-point network', 'selected': 0},
    },
}


class Testdata_frr_2_0_4(MockOPNsenseController):
    def __init__(self):
        super().__init__(key_path=['interface', 'interfaces', 'interface'])
        self.state = {INTERFACE_UUID: INTERFACE.copy()}
        self.areas = {k: v.copy() for k, v in AREAS.items()}
        self.writes = []

    def commands(self) -> dict:
        return {
            'get': self._get,
            'addInterface': self._add,
            'setInterface': self._set,
            'delInterface': self._del,
            'toggleInterface': self._toggle,
            'reconfigure': self._reconfigure,
        }

    def route_kwargs(self, method) -> list:
        return {
            self._get: [],
            self._add: ['data'],
            self._set: ['uuid', 'data'],
            self._del: ['uuid'],
            self._toggle: ['uuid'],
            self._reconfigure: [],
        }[method]

    def _get(self) -> dict:
        # the whole ospf6 model comes back from a single 'get' - the module pulls
        # both 'interfaces.interface' and 'areas.area' out of this one response
        return {
            'ospf6': {
                'enabled': '1',
                'carp_demote': '0',
                'routerid': '192.0.2.1',
                'originate': '0',
                'originatealways': '0',
                'originatemetric': '',
                'areas': {'area': self.areas},
                'interfaces': {'interface': self.state},
                'prefixlists': {'prefixlist': []},
                'routemaps': {'routemap': []},
                'redistributions': {'redistribution': []},
            },
        }

    def _add(self, data: dict) -> dict:
        self.writes.append(('add', None, data))
        return super()._add(data)

    def _set(self, uuid: str, data: dict) -> dict:
        self.writes.append(('set', uuid, data))
        return super()._set(uuid, data)

    def written_areas(self) -> list:
        """The 'area' value of every write that reached the API."""
        return [
            payload['interface']['area']
            for _, _, payload in self.writes
            if 'interface' in payload and 'area' in payload['interface']
        ]
