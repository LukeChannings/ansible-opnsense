from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust import \
    BaseTrust


class Ca(BaseTrust):
    KIND = 'certificate authority'
    API_CONT = 'ca'
    API_KEY_PATH = 'ca'
    EXIST_ATTR = 'ca'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseTrust.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.ca = {}

    def _check_references(self) -> None:
        references = int(self.e['refcount'])

        if references < 1:
            return

        certificates = [
            entry['descr'] for entry in self.api_search_post({
                'module': self.API_MOD,
                'controller': 'cert',
                'command': 'search',
            })
            if entry['caref'] == str(self.e['refid'])
        ]

        if len(certificates) > 0:
            names = "', '".join(certificates)
            linked = f"including the certificate(s): '{names}'"

        else:
            linked = 'by services like OpenVPN or IPsec'

        self.m.fail_json(
            f"The certificate authority '{self.p['description']}' is still referenced "
            f"{references} time(s) in the running config, {linked}. Deleting it would "
            'orphan them - remove the references first or set '
            "'force=true' to delete it anyway."
        )
