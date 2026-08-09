import re

from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.main import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule

CRT_BEGIN = '-----BEGIN CERTIFICATE-----'
CRT_END = '-----END CERTIFICATE-----'
PRV_BEGIN = r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----'
PRV_END = r'-----END (RSA |EC |DSA )?PRIVATE KEY-----'
PRV_BEGIN_ENCRYPTED = '-----BEGIN ENCRYPTED PRIVATE KEY-----'


class BaseTrust(BaseModule):
    KIND = 'certificate'
    FIELD_ID = 'description'
    API_MOD = 'trust'
    API_CONT_REL = 'settings'
    CMDS = {
        'add': 'add',
        'del': 'del',
        'set': 'set',
        'search': 'search',
        'detail': 'get',
    }
    FIELDS_CHANGE = ['certificate', 'private_key']
    FIELDS_ALL = [FIELD_ID, 'action']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TRANSLATE = {
        'description': 'descr',
        'certificate': 'crt_payload',
        'private_key': 'prv_payload',
    }
    FIELDS_TYPING = {
        'select': ['action', 'caref'],
    }
    FIELDS_DIFF_NO_LOG = ['private_key']
    FIELDS_API_NO_LOG = ['prv']
    FIELDS_DIFF_EXCLUDE = ['action']
    TIMEOUT = 30.0

    def check(self) -> None:
        if self.p['state'] == 'present':
            self._check_payloads()

        self._base_check()

        if self.p['state'] == 'present':
            if self.p['private_key'] is None:
                # an omitted private-key keeps whatever is already stored
                self.p['private_key'] = self.e['private_key'] if self.exists else ''

            self.r['diff']['after'] = self.build_diff(data=self.p)

        elif self.exists and not self.p['force']:
            self._check_references()

    def _check_payloads(self) -> None:
        if is_unset(self.p['certificate']):
            self.m.fail_json(
                f"You need to provide a 'certificate' to import a {self.KIND}!"
            )

        self.p['certificate'] = self.p['certificate'].strip()

        if not self.p['certificate'].startswith(CRT_BEGIN) or \
                not self.p['certificate'].endswith(CRT_END):
            self.m.fail_json(
                "The provided 'certificate' has an invalid format - expected a PEM-encoded "
                f"X509 certificate enclosed in '{CRT_BEGIN}' and '{CRT_END}'!"
            )

        if self.p['private_key'] is None:
            return

        self.p['private_key'] = self.p['private_key'].strip()

        if self.p['private_key'] == '':
            return

        if self.p['private_key'].startswith(PRV_BEGIN_ENCRYPTED):
            self.m.fail_json(
                "The provided 'private_key' is passphrase-protected - OPNsense cannot store "
                'encrypted private keys. Decrypt it before importing.'
            )

        if re.match(PRV_BEGIN, self.p['private_key']) is None or \
                re.search(f'{PRV_END} *$', self.p['private_key']) is None:
            self.m.fail_json(
                "The provided 'private_key' has an invalid format - expected a PEM-encoded "
                "private key enclosed in '-----BEGIN PRIVATE KEY-----' and "
                "'-----END PRIVATE KEY-----'!"
            )

    def _check_references(self) -> None:
        raise NotImplementedError('Must be implemented by the inheriting module')

    def get_existing(self) -> list[dict]:
        return [self._redact_private_key(entry) for entry in self._base_get_existing()]

    def _redact_private_key(self, entry: dict) -> dict:
        # the API returns the stored key as PEM ('prv_payload') and base64 ('prv')
        redacted = entry.copy()

        for field in ['private_key', 'prv']:
            if not is_unset(redacted.get(field, '')):
                redacted[field] = self.VALUE_NO_LOG

        return redacted

    def simplify_existing(self, existing: dict) -> dict:
        simple = self._base_simplify_existing(existing)

        for field in ['certificate', 'private_key']:
            simple[field] = str(simple[field]).strip()

        return simple

    def build_request(self) -> dict:
        request = self._base_build_request()

        if is_unset(self.p['private_key']):
            # OPNsense ignores an empty 'prv_payload' - a stored key is only
            # removed by writing the raw field
            request[self.API_KEY_PATH]['prv'] = ''

        return request
