from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.main import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.trust import \
    TRUST_SUBJECT_FIELDS, TRUST_FIELDS_TRANSLATE, PEM_CERT_BEGIN, PEM_CERT_END, \
    certificate_fingerprint
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust import BaseTrust


class Ca(BaseTrust):
    CMDS = {
        'add': 'add',
        'del': 'del',
        'set': 'set',
        'search': 'search',
        'detail': 'get',
        'ca_list': 'ca_list',
    }
    API_KEY_PATH = 'ca'
    API_CONT = 'ca'
    FIELDS_IMMUTABLE = ['ca', 'key_type', 'digest', 'lifetime', 'ocsp_uri', *TRUST_SUBJECT_FIELDS]
    FIELDS_ALL = [*BaseTrust.FIELDS_CHANGE, *FIELDS_IMMUTABLE]
    FIELDS_TRANSLATE = TRUST_FIELDS_TRANSLATE
    FIELDS_TYPING = {
        'select': ['ca', 'key_type', 'digest', 'country'],
    }
    KIND = 'CA'
    # not model-fields: they are carried as the 'existing' action's payloads
    FIELD_FINGERPRINT = 'certificate_fingerprint'

    def _importing(self) -> bool:
        return not is_unset(self.p.get('certificate'))

    def _immutable_fields(self) -> list:
        if self._importing():
            # subject, key-type, digest and validity all come from the imported
            # certificate - the generation-parameters were never used to build it
            return []

        return self.FIELDS_IMMUTABLE

    def check(self) -> None:
        if self.p['state'] == 'present' and not self._importing() and is_unset(self.p.get('country')):
            self.m.fail_json(
                "You need to provide a 'country' to generate a CA - or a 'certificate' to "
                'import an existing one!'
            )

        if self.p['state'] == 'present' and self._importing():
            fingerprint = certificate_fingerprint(self.p['certificate'])
            if fingerprint == '':
                self.m.fail_json(
                    "The provided 'certificate' is not a valid PEM certificate - it must hold a "
                    f"base64 body between '{PEM_CERT_BEGIN}' and '{PEM_CERT_END}'!"
                )

            # compare by fingerprint so a rotated CA is actually rolled out: the
            # API re-wraps the PEM it stores, so the text itself never matches
            self.FIELDS_CHANGE = [*self.FIELDS_CHANGE, self.FIELD_FINGERPRINT]
            self.p[self.FIELD_FINGERPRINT] = fingerprint

        BaseTrust.check(self)

    def simplify_existing(self, existing: dict) -> dict:
        simple = BaseTrust.simplify_existing(self, existing)
        simple[self.FIELD_FINGERPRINT] = certificate_fingerprint(existing.get('crt_payload', ''))
        return simple

    def build_request(self) -> dict:
        request = self._base_build_request()
        payload = request[self.API_KEY_PATH]

        if self._importing():
            payload['action'] = 'existing'
            payload['crt_payload'] = self.p['certificate']
            payload['prv_payload'] = self._import_private_key()
            return request

        if not self.exists:
            payload['action'] = 'internal'
            return request

        # the API re-imports the existing certificate & key on update
        #   using the 'internal' action would generate a new CA!
        detail = self._get_detail()
        payload['action'] = 'existing'
        payload['crt_payload'] = detail['crt_payload']
        payload['prv_payload'] = detail['prv_payload']
        return request

    def _import_private_key(self) -> str:
        if not is_unset(self.p.get('private_key')):
            return self.p['private_key']

        if self.exists:
            # adopting an entry by certificate alone must not throw away a key
            # the firewall already holds for it
            return self._get_detail().get('prv_payload', '')

        return ''

    def delete(self) -> None:
        # the API does not check if the CA is still in use by certificates or services
        if int(self.entry.get('refcount', 0)) > 0:
            self.m.fail_json(
                f"The CA '{self.entry['description']}' is still referenced {self.entry['refcount']} time(s) "
                '(certificates/services) - remove these references first!'
            )

        self._base_delete()
