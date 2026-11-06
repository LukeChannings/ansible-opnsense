from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.base_testdata import \
    MockOPNsenseController

# Synthetic 'get' responses for the OSPF and OSPFv3 area-collections, shaped after
# os-frr 2.0_4 (plugin-commit c4aee28a1, OSPF/OSPF6 model 1.1.5).
#
# Note the shapes the area-model produces:
#  - 'id'                  plain string - the dotted quad
#  - 'ranges'              NetworkField with AsList=Y: one selected option per entry
#  - 'linkedPrefixlist*'   GroupedModelRelationField: option-dict keyed by prefix-list uuid,
#                          with a blank 'None' option because the field is not required
#  - 'type'                OptionField whose blank option means 'normal'

AREA_UUID_BACKBONE = 'a7959b98-d368-4944-aecb-a7915eec0153'
AREA_UUID_NSSA = 'b2ede447-70ed-4f1d-8a73-895311c715ed'
PREFIX_UUID_IN = '7c9e2b10-4d8a-4f33-9b02-66a1d3f5e884'
PREFIX_UUID_OUT = 'b1d0a6f2-55c7-4e19-93aa-0c4f7e21b366'

PREFIX_NAME_IN = 'ANSIBLE_TEST_IN'
PREFIX_NAME_OUT = 'ANSIBLE_TEST_OUT'

PREFIXLISTS = {
    PREFIX_UUID_IN: {
        'enabled': '1',
        'name': PREFIX_NAME_IN,
        'seqnumber': '10',
        'action': {'permit': {'value': 'permit', 'selected': 1}},
        'network': 'any',
    },
    PREFIX_UUID_OUT: {
        'enabled': '1',
        'name': PREFIX_NAME_OUT,
        'seqnumber': '10',
        'action': {'permit': {'value': 'permit', 'selected': 1}},
        'network': 'any',
    },
}


def _as_list_field(values: list) -> dict:
    # NetworkField with AsList=Y - an empty field still renders a single blank option
    if len(values) == 0:
        return {'': {'value': '', 'selected': 1}}

    return {v: {'value': v, 'selected': 1} for v in values}


def _prefixlist_link(selected: str = None) -> dict:
    # GroupedModelRelationField - one option per distinct prefix-list name, keyed by uuid
    options = {'': {'value': 'None', 'selected': 1 if selected is None else 0}}

    for uuid, name in ((PREFIX_UUID_IN, PREFIX_NAME_IN), (PREFIX_UUID_OUT, PREFIX_NAME_OUT)):
        options[uuid] = {'value': name, 'selected': 1 if uuid == selected else 0}

    return options


def _type_field(selected: str, options: list) -> dict:
    return {
        '': {'value': 'normal', 'selected': 1 if selected == '' else 0},
        **{o: {'value': o, 'selected': 1 if o == selected else 0} for o in options},
    }


class _AreaController(MockOPNsenseController):
    """Shared server-side behaviour of ospfsettings/ospf6settings for 'areas.area'."""

    MODEL_KEY = None
    TYPE_OPTIONS = []

    def __init__(self, areas: dict):
        super().__init__(key_path=['area', 'areas', 'area'])
        self.state = {k: v.copy() for k, v in areas.items()}
        self.prefixlists = {k: v.copy() for k, v in PREFIXLISTS.items()}
        self.writes = []

    def commands(self) -> dict:
        return {
            'get': self._get,
            'addArea': self._add,
            'setArea': self._set,
            'delArea': self._del,
            'toggleArea': self._toggle,
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
        # the whole model comes back from a single 'get' - the module pulls both
        # 'areas.area' and 'prefixlists.prefixlist' out of this one response
        return {
            self.MODEL_KEY: {
                'enabled': '1',
                'carp_demote': '0',
                'routerid': '192.0.2.1',
                'areas': {'area': self.state},
                'interfaces': {'interface': []},
                'prefixlists': {'prefixlist': self.prefixlists},
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
        """The area-payload of every write that reached the API."""
        return [payload['area'] for _, _, payload in self.writes if 'area' in payload]


OSPF6_AREAS = {
    AREA_UUID_BACKBONE: {
        'enabled': '1',
        'id': '0.0.0.0',
        'ranges': _as_list_field(['2001:db8:1::/48', '2001:db8:2::/48']),
        'linkedPrefixlistIn': _prefixlist_link(PREFIX_UUID_IN),
        'linkedPrefixlistOut': _prefixlist_link(),
        'type': _type_field('', ['nssa', 'nssa no-summary']),
    },
    AREA_UUID_NSSA: {
        'enabled': '1',
        'id': '0.0.0.1',
        'ranges': _as_list_field([]),
        'linkedPrefixlistIn': _prefixlist_link(),
        'linkedPrefixlistOut': _prefixlist_link(),
        'type': _type_field('nssa', ['nssa', 'nssa no-summary']),
    },
}

OSPF_AREAS = {
    AREA_UUID_BACKBONE: {
        'enabled': '1',
        'id': '0.0.0.0',
        'ranges': _as_list_field(['10.0.1.0/24', '10.0.2.0/24']),
        'linkedPrefixlistIn': _prefixlist_link(PREFIX_UUID_IN),
        'linkedPrefixlistOut': _prefixlist_link(),
        'type': _type_field('', ['stub', 'stub no-summary', 'nssa', 'nssa no-summary']),
    },
    AREA_UUID_NSSA: {
        'enabled': '1',
        'id': '0.0.0.1',
        'ranges': _as_list_field([]),
        'linkedPrefixlistIn': _prefixlist_link(),
        'linkedPrefixlistOut': _prefixlist_link(),
        'type': _type_field('stub', ['stub', 'stub no-summary', 'nssa', 'nssa no-summary']),
    },
}


class Testdata_frr_ospf6_2_0_4(_AreaController):
    MODEL_KEY = 'ospf6'

    def __init__(self):
        super().__init__(areas=OSPF6_AREAS)


class Testdata_frr_ospf_2_0_4(_AreaController):
    MODEL_KEY = 'ospf'

    def __init__(self):
        super().__init__(areas=OSPF_AREAS)
