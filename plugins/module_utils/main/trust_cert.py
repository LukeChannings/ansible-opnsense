from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.main import \
    is_true
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust import \
    BaseTrust


class Cert(BaseTrust):
    KIND = 'certificate'
    API_CONT = 'cert'
    API_KEY_PATH = 'cert'
    EXIST_ATTR = 'cert'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseTrust.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.cert = {}

    def _check_references(self) -> None:
        if not is_true(self.e['in_use']):
            return

        self.m.fail_json(
            f"The certificate '{self.p['description']}' is currently in use by a service - "
            'deleting it would leave that service without a certificate. Remove the '
            "reference first or set 'force=true' to delete it anyway."
        )
