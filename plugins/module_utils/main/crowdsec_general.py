from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_ip, validate_str_fields
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import GeneralModule


class General(GeneralModule):
    CMDS = {
        'set': 'set',
        'search': 'get',
    }
    API_KEY_PATH = 'general'
    API_KEY_PATH_REQ = API_KEY_PATH
    API_MOD = 'crowdsec'
    API_CONT = 'general'
    API_CONT_REL = 'service'
    API_CMD_REL = 'reconfigure'
    FIELDS_CHANGE = [
        'agent_enabled', 'lapi_enabled', 'firewall_bouncer_enabled',
        'lapi_manual_configuration', 'lapi_listen_address', 'lapi_listen_port',
        'rules_enabled', 'rules_log', 'rules_tag', 'enroll_key',
        'crowdsec_firewall_verbose',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    FIELDS_DIFF_NO_LOG = ['enroll_key']
    FIELDS_TYPING = {
        'bool': [
            'agent_enabled', 'lapi_enabled', 'firewall_bouncer_enabled',
            'lapi_manual_configuration', 'rules_enabled', 'rules_log',
            'crowdsec_firewall_verbose',
        ],
        'int': ['lapi_listen_port'],
    }
    INT_VALIDATIONS = {
        'lapi_listen_port': {'min': 1, 'max': 65535},
    }
    MASK_ALPHANUM = r'^[0-9a-zA-Z]{1,63}$'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)

    def check(self) -> None:
        if not is_ip(self.p['lapi_listen_address']):
            self.m.fail_json(
                f"Value '{self.p['lapi_listen_address']}' is not a valid IP-Address "
                "for the local API to listen on!"
            )

        validate_str_fields(
            module=self.m,
            data=self.p,
            field_regex={
                'rules_tag': self.MASK_ALPHANUM,
                'enroll_key': self.MASK_ALPHANUM,
            },
            allow_empty=True,
        )

        if self.p['enroll_key'] is None:
            self.p.pop('enroll_key')

        self._base_check()
